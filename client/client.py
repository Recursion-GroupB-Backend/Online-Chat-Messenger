import socket
import threading
import time

class Client:
    NAME_SIZE = 255
    BUFFER_SIZE = 4096

    def __init__(self, server_address='0.0.0.0', server_port=9001):
        self.client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_address = server_address
        self.server_port = server_port
        self.user_name = ''
        self.name_size = 0

    def start(self):
        self.create_user()
        thread_send = threading.Thread(target=self.send_message, daemon=True)
        thread_send.start()
        thread_recieve_message = threading.Thread(target=self.receive_message, daemon=True)
        thread_recieve_message.start()  

    def create_user(self):
        while True:
            user_name = input('Enter your name: ')
            if (len(user_name.encode()) > Client.NAME_SIZE):
                print(f'Your name must equal to less than {Client.NAME_SIZE} bytes')
                continue
            self.name_size = len(user_name)
            self.user_name = user_name
            break

    def send_message(self):
        try:
            print('Enter your message')
            while True:
                message = input()
                if (len(message.encode()) + self.name_size + 1> client.BUFFER_SIZE):
                    print(f'Messeges must be equal to or less than {Client.BUFFER_SIZE} bytes')
                    continue
                message_byte = self.message_encode(message)
                # Todo:ここでメッセージを送信するためのひな型（プロンプト）に書き換えてから送信する
                self.client_sock.sendto(message_byte, (self.server_address, self.server_port))
        finally:
            print('socket closig....')
            self.client_sock.close()

    def message_encode(self, message:str):
        # 最初の1バイトをユーザー名のサイズとして作成して、その後にユーザ名、メッセージのプロンプトにする関数
        # サーバーは最初の1バイト(ユーザー名のサイズ)を読み込んでユーザー名を特定し、ユーザー名とメッセージを受信することができるようにする。
        name_len_byte  = self.name_size.to_bytes(1, byteorder='big')
        name_byte      = self.user_name.encode('utf-8')
        message_byte   = message.encode('utf-8')
        return name_len_byte + name_byte + message_byte

    def receive_message(self):
        try:
            while True:    
                message, _ = self.client_sock.recvfrom(4096)
                print(message.decode('utf-8'))
        finally:
            print('socket closing')
            self.client_sock.close()
    def shutdown(self):
        print("Client is shutting down.")
        self.client_sock.close()
        # その他のクリーンアップ処理があればここに追加

if __name__ == "__main__":
    client = Client()
    client.start()
    try:
        while True:  # メインスレッドをアクティブに保つ
            time.sleep(1)
    except KeyboardInterrupt:
        client.shutdown()