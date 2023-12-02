import socket
import threading
import time

class User:
    def __init__(self, user_name, address, token, member_type):
        self.user_name = user_name
        self.address = address
        self.token = token
        self.last_active = time.time()
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.member_type = member_type

    # def send_message(self):

class ChatRoom:
    def __init__(self, room_name):
        self.room_name = room_name
        self.users = {}

    # user追加
    def add_user(self, client_id, client: User):
        self.users[client_id] = client

    # user削除
    def remove_user(self, client_id):
        if client_id in self.users:
            del self.users[client_id]

    # 参加者にメッセージを送信
    def broadcast(self, message, self_address=None):
        for address, user in self.users.items():
            if (self_address == address):
                pass
            else:
                user.send_message(message, address)

    def check_timeout(self):
        try:
            while True:
                current_time = time.time()
                for address, user in self.users.items():
                    if current_time - user['last_active'] > self.TIMEOUT:
                        username = user['username']
                        print(f"Client {username} ({address}) has timed out.")
                        timeout_message = f"{username} has timed out and left the chat.".encode('utf-8')
                        self.broadcast(timeout_message)
                        self.users.pop(address, None)
                time.sleep(10)
        finally:
            print('socket closig....')
            # self.server_sock.close()

class Server:
    def __init__(self):
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_sock.bind(('0.0.0.0', 9001))
        self.clients = {}
        self.TIMEOUT = 60

    def start(self):
        # 同時にメッセージ受信とクライアントのタイムアウト監視を行うことで効率的な並行処理が可能になる。
        thread_check_timeout    = threading.Thread(target=self.check_client_timeout, daemon=True)
        thread_check_timeout.start()
        thread_recieve_message  = threading.Thread(target=self.recieve_message, daemon=True)
        thread_recieve_message.start()
    def recieve_message(self):
        try:
            while True:
                print('\nwaiting to receive message')
                # データの取得（データを受け取るまで処理は止まる）
                data, address = self.server_sock.recvfrom(4096)

                # 取得データを適切に処理
                username_len = int.from_bytes(data[:1], byteorder='big')
                username = data[1:1 + username_len].decode('utf-8')
                message_for_send = f"{username}: {data[1 + username_len:].decode('utf-8')}"

                # サーバーに参加しているクライアントを管理
                self.clients[address] = {'username':username,'last_time': time.time()}

                # 接続されている全てのクライアントにメッセージを送信
                self.broadcast(message_for_send.encode('utf-8'), address)

        finally:
            print('socket closig....')
            self.server_sock.close()

    def broadcast(self, message:bytes, self_address=None):
        for address in self.clients:
            if (self_address == address):
                # クライアントが自分自身で送信したメッセージは本人には返さない。
                pass
            else:
                self.server_sock.sendto(message, address)

    def check_client_timeout(self):
        try:
            while True:
                current_time = time.time()
                for address, client_data in self.clients.items():
                    if current_time - client_data['last_time'] > self.TIMEOUT:
                        username = client_data['username']
                        print(f"Client {username} ({address}) has timed out.")
                        timeout_message = f"{username} has timed out and left the chat.".encode('utf-8')
                        self.broadcast(timeout_message)
                        self.clients.pop(address, None)
                time.sleep(10)  # 10秒ごとに監視
        finally:
            print('socket closig....')
            self.server_sock.close()

    def shutdown(self):
        print("Server is shutting down.")
        self.server_sock.close()
        # その他のクリーンアップ処理があればここに追加

if __name__ == "__main__":
    server = Server()
    server.start()
    try:
        while True:  # メインスレッドをアクティブに保つ
            time.sleep(1)
    except KeyboardInterrupt:
        server.shutdown()
