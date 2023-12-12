import time
import struct
from server.user import User

class ChatRoom:
    TIME_OUT = 20

    def __init__(self, room_name):
        self.room_name = room_name
        self.users = {}

    # user追加
    def add_user(self, client: User):
        self.users[client.token] = client

    # user削除
    def remove_user(self, client: User):
        if client.token in self.users:
            del self.users[client.token]

    # 参加者にメッセージを送信
    def broadcast(self, message, token, udp_socket):

        send_user = self.users[token]
        user_name_encoded = send_user.user_name.encode('utf-8')
        message_encoded = message.encode('utf-8')

        # チャットルーム内の全ユーザーにメッセージを送信
        for user_token, user in self.users.items():
            # ヘッダーの作成
            user_name_size = len(user_name_encoded)
            message_size = len(message_encoded)
            header = struct.pack('!BB', user_name_size, message_size)

            full_message = header + user_name_encoded + message_encoded

            udp_socket.sendto(full_message, user.udp_address)

    def broadcast_remove_message(self, remove_client: User, udp_socket, is_timeout = False):

        # チャットルーム内の全ユーザーにメッセージを送信
        send_user = self.users[remove_client.token]
        user_name_encoded = send_user.user_name.encode('utf-8')
        if is_timeout:
            message = f"{remove_client.user_name} has timed out and left the {self.room_name}."
        else:
            message = f"{remove_client.user_name} has left the {self.room_name}."

        message_encoded = message.encode('utf-8')

        for token, user in list(self.users.items()):
            if token == remove_client.token:
                if user.member_type == "guest":
                    self.remove_user(remove_client)
                # TODO user.member_typeがhostの場合の処理を追加
                # else:
                pass
            else:
                # ヘッダーの作成
                user_name_size = len(user_name_encoded)
                message_size = len(message_encoded)
                header = struct.pack('!BB', user_name_size, message_size)

                full_message = header + user_name_encoded + message_encoded
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
