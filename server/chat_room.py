import time
from server.user import User

class ChatRoom:
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
    def broadcast(self, message, self_address=None):
        for address, user in self.users.items():
            if (self_address == address):
                pass
            else:
                user.send_message(message, address)

    def broadcast_remove_message(self, remove_client: User, udp_socket):
        for token, user in self.users.items():
            if token == remove_client.token:
                self.remove_user(remove_client)
                pass
            else:
                message = f"{user.username} has left {self.room_name}."

            remove_msg = {
                "room_name": self.room_name,
                "username": user.user_name,
                "message": message
            }
            udp_socket.sendto(remove_msg, user.address)

    def check_timeout(self):
        try:
            while True:
                current_time = time.time()
                for token, user in self.users.items():
                    if current_time - user['last_active'] > self.TIMEOUT:
                        username = user['username']
                        print(f"Client {username} ({token}) has timed out.")
                        timeout_message = f"{username} has timed out and left the chat.".encode('utf-8')
                        self.broadcast(timeout_message)
                        self.remove_user(user)
                time.sleep(10)
        finally:
            print('socket closig....')
            # self.server_sock.close()
