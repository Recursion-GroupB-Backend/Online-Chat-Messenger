import time
import struct
from server.user import User

class ChatRoom:
    TIME_OUT = 3

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

            udp_socket.sendto(full_message, user.address)

    def broadcast_remove_message(self, remove_client: User, udp_socket):

        # チャットルーム内の全ユーザーにメッセージを送信
        send_user = self.users[remove_client.token]
        user_name_encoded = send_user.user_name.encode('utf-8')
        message = f"{remove_client.user_name} has left {self.room_name}."
        message_encoded = message.encode('utf-8')

        for token, user in list(self.users.items()):
            if token == remove_client.token:
                if user.member_type == "guest":
                    self.remove_user(remove_client)
                # user.member_typeがhostの場合の処理を追加
                # else:
                pass
            else:
                # ヘッダーの作成
                user_name_size = len(user_name_encoded)
                message_size = len(message_encoded)
                header = struct.pack('!BB', user_name_size, message_size)

                full_message = header + user_name_encoded + message_encoded
                udp_socket.sendto(full_message, user.address)

    def check_timeout(self, udp_socket):
        try:
            while True:
                current_time = time.time()
                for token, user in list(self.users.items()):
                    if current_time - user['last_active'] > self.TIMEOUT:
                        username = user['username']
                        print(f"Client {username} ({token}) has timed out.")
                        timeout_message = f"{username} has timed out and left the chat.".encode('utf-8')
                        self.broadcast(timeout_message, token, udp_socket)
                        self.remove_user(user)
                time.sleep(10)
        finally:
            print('socket closig....')
            # self.server_sock.close()
