import socket
import threading
import time
import struct
import json
from constants.operation import Operation

class Client:
    NAME_SIZE = 255
    ROOM_NAME_SIZE = 255
    HEADER_SIZE = 32
    BUFFER_SIZE = 4096
    CREATE_ROOM = 1
    JOIN_ROOM = 2

    def __init__(self, server_address='0.0.0.0'):
        self.udp_client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tcp_client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address  = server_address
        self.tcp_server_port = 9000
        self.udp_server_port = 9001
        self.user_name = ''
        self.name_size = 0
        self.room_name = ''
        self.operation_code = 0
        self.state = 0
        self.password = ''
        self.token = ''

    def start(self):
        self.input_username()
        self.tcp_connect_server()
        thread_send = threading.Thread(target=self.udp_send_message, daemon=True)
        thread_send.start()
        thread_recieve_message = threading.Thread(target=self.receive_message, daemon=True)
        thread_recieve_message.start()  

    def input_username(self):
        while True:
            user_name = input('Enter your name: ')
            if (len(user_name.encode()) > Client.NAME_SIZE):
                print(f'Your name must equal to less than {Client.NAME_SIZE} bytes')
                continue
            self.name_size = len(user_name)
            self.user_name = user_name
            break

    def tcp_connect_server(self):
        try:
            self.tcp_client_sock.connect((self.server_address, self.tcp_server_port))
            custom_tcp_request = self.create_tcp_request()
            self.tcp_client_sock.sendall(custom_tcp_request)
            self.receive_tcp_response()
        except Exception as e:
            print(f"An error occurred while connecting to the server: {e}")

    def create_tcp_request(self):

        # ルーム作成 or 参加の指定
        while True:
            print("1. Create a new room\n"
                "2. Join room\n")
            try:
                print("Please enter 1 or 2 : ")
                self.operation_code = int(input())
                if int(self.operation_code) in [Operation.CREATE_ROOM.value, Operation.JOIN_ROOM.value]:
                    break
            except Exception:
                continue
        
        # ルーム名の記入
        while True:
            self.room_name = input('Enter room name: ')
            # ルーム名のサイズ確認
            if len(self.room_name) > Client.ROOM_NAME_SIZE:
                print(f"Your name must equal to less than {Client.ROOM_NAME_SIZE} bytes")
                continue
            # stage3で使うため一旦、コメントアウト
            # self.password = input('Enter PassWord: ')
            break
                
        # 必要に応じてパスワードなどを追加する
        operation_payload = {"user_name":self.user_name}
        
        
        return self.create_tcp_protocol(operation_payload)
    
    def create_tcp_protocol(self, operation_payload: dict):

        # ペイロードをJSON文字列に変換し、バイト列にエンコード
        operation_payload_bytes = json.dumps(operation_payload).encode('utf-8')
        operation_payload_size_bytes = len(operation_payload_bytes).to_bytes(29, 'big')
        
        """
        送信プロトコル確認用：後で削除
        """
        print("-------- リクエスト   -----------")
        print("Room Name:", self.room_name)
        print("User Name:", self.user_name)
        print("Operation:", self.operation_code)
        print("State:", self.state)
        print("Payload:", operation_payload)
        print("-------- リクエスト ---------")
        
        header = struct.pack('!B B B 29s', len(self.room_name), self.operation_code, self.state, operation_payload_size_bytes)
        body = self.room_name.encode('utf-8') + operation_payload_bytes
        return header + body
    
    def receive_tcp_response(self):

        while True:
            header_bytes = self.tcp_client_sock.recv(Client.HEADER_SIZE)
            room_name_size = header_bytes[0]
            operation_code = header_bytes[1]
            response_state = header_bytes[2]
            operation_payload_size = int.from_bytes(header_bytes[3:], 'big')
            
            body_bytes = self.tcp_client_sock.recv(room_name_size + operation_payload_size)
            self.room_name = body_bytes[:room_name_size].decode('utf-8')
            operation_payload = json.loads(body_bytes[room_name_size:].decode('utf-8'))

            """
            受信プロトコル確認用：後で削除
            """
            print("-------- レスポンス   -----------")
            print(f'room_name_size: {room_name_size}')
            print(f'operation_code: {operation_code}')
            print(f'State: {response_state}')
            print(f'room_name: {self.room_name}') 
            print(f'Payload: {operation_payload}') 
            print("-------- レスポンス   -----------")
            
            if response_state == 2:
                self.token = operation_payload['token']
                print(operation_payload['message'])
            else:
                # operation_payload_bytesが空でないことを確認
                if not operation_payload:
                    print("No payload received, or the connection was closed.")
                    break
                print(operation_payload['message'])    
            self.tcp_client_sock.close()
            break
    
    def send_message(self):
        try:
            print('Enter your message')
            while True:
                message = input()
                # 送信サイズの確認
                if (2 + len(self.room_name) + len(self.token) + len(message.encode()) > client.BUFFER_SIZE):
                    print(f'Messeges must be equal to or less than {Client.BUFFER_SIZE} bytes')
                    continue
                message_byte = self.udp_message_encode(message)
                self.udp_client_sock.sendto(message_byte, (self.server_address, self.udp_server_port))
                print("メッセージを送信")
        finally:
            print('socket closig....')
            self.udp_client_sock.close()
    
    def udp_message_encode(self, message:str):
        # ヘッダー[2BYTE] + ボディ[ルーム名 + トークン + メッセージ]
        header = struct.pack('!B B', len(self.room_name), len(self.token))
        
        room_name_byte  = self.room_name.encode('utf-8')
        token_byte      = self.token.encode('utf-8')
        message_byte    = message.encode('utf-8')
        
        body   = room_name_byte + token_byte + message_byte
        
        return header + body
    
    def receive_message(self):
        try:
            while True:
                message, _ = self.udp_client_sock.recvfrom(4096)
                print(f"受信メッセージ：{message.decode('utf-8')}")
        finally:
            print('socket closing')
            self.udp_client_sock.close()
            
    def shutdown(self):
        print("Client is shutting down.")
        self.udp_client_sock.close()
        # その他のクリーンアップ処理があればここに追加

if __name__ == "__main__":
    client = Client()
    client.start()
    try:
        while True:  # メインスレッドをアクティブに保つ
            time.sleep(1)
    except KeyboardInterrupt:
        client.shutdown()