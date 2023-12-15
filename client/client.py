import socket
import threading
import time
import struct
import json
from constants.operation import Operation
from cryptography.hazmat.primitives import serialization, asymmetric, hashes
from cryptography.hazmat.primitives.asymmetric import padding

class Client:
    NAME_SIZE = 255
    ROOM_NAME_SIZE = 255
    HEADER_SIZE = 32
    BUFFER_SIZE = 4096

    def __init__(self, server_address = '127.0.0.1'):
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
        self.client_public_key = ''
        self.client_private_key = ''
        self.server_public_key = ''

        self.udp_client_sock.bind((self.server_address, 0))
        self.udp_client_address = (self.udp_client_sock.getsockname()[0], self.udp_client_sock.getsockname()[1])
        self.generate_rsa_key_pair()

    def start(self):
        self.input_username()
        self.tcp_connect_server()
        thread_send = threading.Thread(target=self.udp_send_message, daemon=True)
        thread_send.start()
        thread_recieve_message = threading.Thread(target=self.udp_receive_message, daemon=True)
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
        self.operation_code = self.prompt_for_operation_code()
        self.room_name = self.prompt_for_room_name()
        self.password = self.prompt_for_password()

        operation_payload = {
            "user_name":self.user_name,
            "ip": self.udp_client_address[0],
            "port": self.udp_client_address[1],
            "password": self.password,
            "public_key": self.encode_pem(self.client_public_key)
        }

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
                public_key_pem = operation_payload.get("public_key")
                self.server_public_key = serialization.load_pem_public_key(public_key_pem.encode('utf-8'))
                print(operation_payload['message'])
            else:
                # operation_payload_bytesが空でないことを確認
                if not operation_payload:
                    print("No payload received, or the connection was closed.")
                    break
                print(operation_payload['message'])
                self.shutdown()

            self.tcp_client_sock.close()
            break

    def udp_send_message(self):
        try:
            print('Enter your message')
            while True:
                message = input()
                encrypted_message = self.encrypt_message(message)

                # 送信サイズの確認
                if (2 + len(self.room_name) + len(self.token) + len(encrypted_message) > Client.BUFFER_SIZE):
                    print(f'Encrypted messages must be equal to or less than {Client.BUFFER_SIZE} bytes')
                    continue
                message_byte = self.udp_message_encode(encrypted_message)
                self.udp_client_sock.sendto(message_byte, (self.server_address, self.udp_server_port))

        except Exception as e:
            print(f"Error sending message: {e}")

        finally:
            print('socket closing....')
            self.udp_client_sock.close()

    def udp_message_encode(self, message_byte:bytes):
        # ヘッダー[2BYTE] + ボディ[ルーム名 + トークン + メッセージ]
        header = struct.pack('!B B', len(self.room_name), len(self.token))

        room_name_byte  = self.room_name.encode('utf-8')
        token_byte      = self.token.encode('utf-8')

        body   = room_name_byte + token_byte + message_byte

        return header + body

    def udp_receive_message(self):
        try:
            while True:
                data, _ = self.udp_client_sock.recvfrom(4096)

                user_name_size, message_size = struct.unpack('!HH', data[:4])
                encrypted_user_name = data[4: 4 + user_name_size]
                # 暗号化されたユーザー名とメッセージを復号化
                encrypted_message = data[4 + user_name_size: 4 + user_name_size + message_size]

                try:
                    decrypted_user_name = self.decrypt_message(encrypted_user_name).decode('utf-8')
                    decrypted_message = self.decrypt_message(encrypted_message).decode('utf-8')
                    if "exit" == decrypted_message:
                        print("The host has closed the chat room.")
                        self.shutdown()
                    if decrypted_user_name != self.user_name:
                        print(f"{decrypted_user_name}：{decrypted_message}")
                except Exception as e:
                    print(f"Error decrypting message: {e}")
                    continue



        except OSError:
            pass
        finally:
            print('socket closing')
            self.udp_client_sock.close()



    def prompt_for_operation_code(self):
        while True:
            print("1. Create a new room\n2. Join room")
            try:
                operation_code = int(input("Please enter 1 or 2: "))
                if operation_code in [Operation.CREATE_ROOM.value, Operation.JOIN_ROOM.value]:
                    return operation_code
            except ValueError:
                print("Invalid input. Please enter 1 or 2.")

    def prompt_for_room_name(self):
        while True:
            room_name = input('Enter room name: ')
            if len(room_name) <= Client.ROOM_NAME_SIZE:
                return room_name
            print(f"Your name must be less than {Client.ROOM_NAME_SIZE} bytes")

    def prompt_for_password(self):
        while True:
            password = input('Enter Password: ')
            if len(password) < 6:
                print("Password must be at least 6 characters long.")
            elif not any(char.isdigit() for char in password):
                print("Password must contain at least one digit.")
            elif not any(char.isalpha() for char in password):
                print("Password must contain at least one letter.")
            else:
                return password

    def generate_rsa_key_pair(self):
        self.client_private_key = asymmetric.rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )

        self.client_public_key = self.client_private_key.public_key()

    def encode_pem(self, client_public_key):
        return client_public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

    def encrypt_message(self, message):
        encrypted_message = self.server_public_key.encrypt(
            message.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return encrypted_message

    def decrypt_message(self, encrypted_message):
        return self.client_private_key.decrypt(
            encrypted_message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )


    def shutdown(self):
        encrypted_exit_message = self.encrypt_message("exit")
        message_byte = self.udp_message_encode(encrypted_exit_message)
        self.udp_client_sock.sendto(message_byte, (self.server_address, self.udp_server_port))
        print("Client is shutting down.")
        self.udp_client_sock.close()
        self.tcp_client_sock.close()
        exit()


if __name__ == "__main__":
    client = Client()
    client.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        client.shutdown()
