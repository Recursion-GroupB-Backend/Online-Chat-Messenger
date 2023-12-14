import socket
import threading
import time
import struct
import json
import secrets
import re
from constants.operation import Operation
from constants.member_type import MemberType
from server.user import User
from server.chat_room import ChatRoom
from cryptography.hazmat.primitives import serialization, asymmetric, hashes
from cryptography.hazmat.primitives.asymmetric import padding



class Server:
    HEADER_MAX_BITE = 32
    TOKEN_MAX_BITE = 80
    MAX_MESSAGE_SIZE = 4096

    def __init__(self, tcp_address = "127.0.0.1", udp_address = "127.0.0.1"):
        self.tcp_address = tcp_address
        self.udp_address = udp_address
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.tcp_socket.bind((self.tcp_address, 9000))
        self.udp_socket.bind((self.udp_address, 9001))
        self.clients = {}
        self.rooms = {}
        self.TIMEOUT = 60
        self.server_public_key = ''
        self.server_private_key = ''

        self.generate_rsa_key_pair()


    def start(self):
        thread_handle_tcp = threading.Thread(target=self.wait_to_tcp_connections, daemon=True)
        thread_handle_tcp.start()

        # TODO: UDP通信や他の要件はissue毎にコメント外していく
        thread_receive_udp_message = threading.Thread(target=self.receive_udp_message, daemon=True)
        thread_receive_udp_message.start()
        thread_check_timeout = threading.Thread(target=self.remove_inactive_users, daemon=True)
        thread_check_timeout.start()


    def wait_to_tcp_connections(self):
        self.tcp_socket.listen(1)
        while True:
            print('\nwaiting to receive tcp connect')
            client_socket, addr = self.tcp_socket.accept()
            thread = threading.Thread(target=self.establish_tcp_connect, args=(client_socket, addr,))
            thread.start()

    def establish_tcp_connect(self, client_socket, tcp_address):
        try:
            room_name, user_name, operation, state, payload = self.receive_tcp_message(client_socket)

            # stateを処理中に更新
            state =  1

            print("-------- receive request value   -----------")
            print("Room Name:", room_name)
            print("User Name:", user_name)
            print("Operation:", operation)
            print("State:", state)
            print("Payload:", payload)
            print("payload address", (payload['ip'], payload['port']))
            print("tcp_address", tcp_address)
            print("-------- receive request value end ---------")

            user = self.create_user(
                user_name,
                tcp_address,
                (payload['ip'], payload['port']),
                operation,
                payload['public_key']
            )

            print("ユーザー作成の完了")

            operation_response = {}
            if operation == Operation.CREATE_ROOM.value:
                operation_response = self.create_room(user, room_name, payload['password'])
            elif operation == Operation.JOIN_ROOM.value:
                operation_response = self.join_room(user, room_name, payload['password'])

            print(operation_response)
            # 状態を更新
            if operation_response["status"] in [200, 201]:
                state = 2

            public_key_pem = self.encode_pem(self.server_public_key)

            # TCPレスポンスを返す
            self.send_tcp_response(client_socket, operation, state, operation_response, room_name, public_key_pem, user.token)


        except Exception as e:
            print("Error in receive_tcp_message:", e)

    def send_tcp_response(self, client_socket, operation, state, operation_response, room_name, public_key_pem, token = None):
        """クライアントにレスポンスを送信する"""
        try:
            payload = {
                "status": operation_response["status"],
                "message": operation_response["message"],
                "token": token,
                "public_key": public_key_pem
            }

            payload_json = json.dumps(payload)
            payload_bytes = payload_json.encode('utf-8')
            room_name_bytes = room_name.encode('utf-8')

            header = struct.pack('!B B B 29s', len(room_name), operation, state, len(payload_bytes).to_bytes(29, 'big'))
            body = room_name_bytes + payload_bytes

            client_socket.sendall(header + body)

        except Exception as e:
            print(f"Error in send_response: {e}")

        finally:
            print('tcp socket closing....')
            client_socket.close()


    def receive_tcp_message(self, client_socket):
        """TCPメッセージのヘッダーとペイロードを受信"""
        header = client_socket.recv(self.HEADER_MAX_BITE)
        room_name_size, operation, state, operation_payload_size = struct.unpack('!B B B 29s', header)

        room_name = client_socket.recv(room_name_size)
        room_name = room_name.decode()

        operation_payload = client_socket.recv(int.from_bytes(operation_payload_size, 'big'))
        operation_payload = json.loads(operation_payload)

        user_name = operation_payload["user_name"]

        return room_name, user_name, operation, state, operation_payload

    def generate_token(self):
        return secrets.token_hex(self.TOKEN_MAX_BITE)


    def receive_udp_message(self):
        try:
            while True:
                print('\nwaiting to receive message')

                data, address = self.udp_socket.recvfrom(self.MAX_MESSAGE_SIZE)

                # ヘッダーを解析
                room_name_size = data[0]
                token_size = data[1]

                # ボディを抽出
                start = 2
                room_name = data[start:start + room_name_size].decode('utf-8')
                start += room_name_size
                token = data[start:start + token_size].decode('utf-8')
                start += token_size
                encrypted_message = data[start:]

                # 暗号化されたメッセージを復号化
                try:
                    decrypted_message = self.decrypt_message(encrypted_message)

                except Exception as e:
                    print(f"Error decrypting message: {e}")
                    continue

                # デバッグログ
                print(f"room name: {room_name}, token: {token}, message: {decrypted_message}")

                # userが退出した時の処理
                if decrypted_message == "exit":
                    room = self.rooms[room_name]
                    room.broadcast_remove_message(room.users[token], self.udp_socket)
                    pass
                else:
                    if not self.valid_user(token, address, room_name):
                        raise Exception("Invalid user or token mismatch")

                    # TODO: # last_activeの更新などの処理を
                    self.rooms[room_name].broadcast(decrypted_message, token, self.udp_socket)


        except Exception as e:
            print(f'receive error message: {e}')
            self.udp_socket.close()


    def valid_user(self, token, address, room_name):
        if self.rooms.get(room_name) is not None:
            room = self.rooms[room_name]

            # トークンがルームのユーザー辞書に含まれているか確認
            if room.users.get(token) is not None:
                user = room.users[token]

            # トークンに紐づくユーザーのIPアドレスが引数のアドレスと一致するか確認
            if user.udp_address[0] == address[0] and user.token == token:
                return True

        return False

    def create_room(self, user, room_name, password):
        validation_message = self.is_valid_password(password)
        if validation_message:
            return {"status": 400, "message": validation_message}

        if self.rooms.get(room_name) is None:
            chat_room = ChatRoom(room_name, password)
            chat_room.add_user(user)
            self.rooms[room_name] = chat_room
            return {"status": 200, "message": "Chat room created successfully."}
        else:
            return {"status": 400, "message": "Chat room already exists."}

    def create_user(self, user_name, tcp_address, udp_address, operation, public_key_pem):
        return User(
            user_name,
            tcp_address,
            udp_address,
            self.generate_token(),
            MemberType.HOST.value if operation == Operation.CREATE_ROOM.value else MemberType.GUEST.value,
            serialization.load_pem_public_key(public_key_pem.encode('utf-8'))
        )

    def join_room(self, user, room_name, password):
        room = self.rooms.get(room_name)
        if room is not None:
            if room.password != password:
                return {"status": 401, "message": "Incorrect password."}
            else:
                room.add_user(user)
                return {"status": 200, "message": "Joined chat room successfully."}
        else:
            return {"status": 404, "message": "Chat room not found."}

    def remove_inactive_users(self):
        while True:
            for room_name, room in self.rooms.items():
                room.check_timeout(self.udp_socket)
                # デバッグ出力: 各ルームのユーザー一覧
                print(f"Room '{room_name}' users:")

            print("10秒後に再びタイムアウトチェックを行います")
            time.sleep(10)

    def is_valid_password(self, password):
        if len(password) < 6:
            return "Password must be at least 6 characters long."
        if not re.search("[0-9]", password):
            return "Password must contain at least one digit."
        if not re.search("[a-zA-Z]", password):
            return "Password must contain at least one letter."
        return None

    def generate_rsa_key_pair(self):
        self.server_private_key = asymmetric.rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )

        self.server_public_key = self.server_private_key.public_key()

    def encode_pem(self, server_public_key):
        return server_public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

    def decrypt_message(self, encrypted_message):
        return self.server_private_key.decrypt(
            encrypted_message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    def shutdown(self):
        print("Server is shutting down.")
        self.udp_socket.close()
        # その他のクリーンアップ処理があればここに追加

if __name__ == "__main__":
    server = Server()
    server.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.shutdown()
