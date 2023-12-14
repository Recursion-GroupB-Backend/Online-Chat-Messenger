import time
import struct
from server.user import User
from cryptography.hazmat.primitives import serialization, asymmetric, hashes
from cryptography.hazmat.primitives.asymmetric import padding

class ChatRoom:
    TIME_OUT = 20

    def __init__(self, room_name, password):
        self.room_name = room_name
        self.password = password
        self.users = {}

    # user追加
    def add_user(self, client: User):
        self.users[client.token] = client

    # user削除
    def remove_user(self, client: User):
        if client.token in self.users:
            del self.users[client.token]

    def broadcast(self, decrypted_message, token, udp_socket):
        send_user = self.users[token]

        user_name_encoded = send_user.user_name.encode('utf-8')

        for user_token, user in self.users.items():
            # 各ユーザーの公開鍵で暗号化
            encrypted_user_name = self.encrypt_message(user_name_encoded, user.public_key)
            encrypted_message = self.encrypt_message(decrypted_message, user.public_key)

            # ヘッダー作成
            user_name_size = len(encrypted_user_name)
            message_size = len(encrypted_message)
            header = struct.pack('!HH', user_name_size, message_size)

            full_message = header + encrypted_user_name + encrypted_message
            print("Sending message", full_message)

            udp_socket.sendto(full_message, user.udp_address)

    def broadcast_remove_message(self, remove_clients: User, udp_socket, is_timeout = False):
        # チャットルーム内の全ユーザーにメッセージを送信
        send_user = self.users[remove_clients.token]
        user_name_encoded = send_user.user_name.encode('utf-8')

        if is_timeout:
            message = f"{remove_clients.user_name} has timed out and left the {self.room_name}."
        else:
            message = f"{remove_clients.user_name} has left the {self.room_name}."

        for token, user in list(self.users.items()):
            if token == remove_clients.token:
                if user.member_type == "guest":
                    self.remove_user(remove_clients)
                # TODO user.member_typeがhostの場合の処理を追加
                # else:
                pass
            else:
                # 各ユーザーの公開鍵で暗号化
                encrypted_user_name = self.encrypt_message(user_name_encoded, user.public_key)
                encrypted_message = self.encrypt_message(message.encode('utf-8'), user.public_key)

                # ヘッダー作成
                user_name_size = len(encrypted_user_name)
                message_size = len(encrypted_message)
                header = struct.pack('!HH', user_name_size, message_size)

                full_message = header + encrypted_user_name + encrypted_message
                print("Exiting message sending", full_message)

                udp_socket.sendto(full_message, user.udp_address)


    def check_timeout(self, udp_socket):
        timeout_users = []
        current_time = time.time()
        for token, user in list(self.users.items()):
            if current_time - user.last_active > self.TIME_OUT:
                timeout_users.append(user)

        for user in timeout_users:
            self.broadcast_remove_message(user, udp_socket, True)
            print(f"{user.user_name} 削除完了")

    def encrypt_message(self, message, client_public_key):
        encrypted_message = client_public_key.encrypt(
            message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return encrypted_message
