import socket
import threading
import time
import struct
import json
import secrets
from constants.operation import Operation
from constants.member_type import MemberType
from server.user import User
from server.chat_room import ChatRoom



class Server:
    TIME_OUT = 60
    HEADER_MAX_BITE = 32
    TOKEN_MAX_BITE = 128

    STATUS_MESSAGE = {
        200: 'Successfully joined a chat room',
        201: 'Successfully create a chat room',
        202: 'Server accpeted your request',
        401: 'Token or room password is invalid',
        404: 'Requested chat room does not exist',
        409: 'Requested room name or username already exists',
    }

    def __init__(self, tcp_address = "0.0.0.0", udp_address = "0.0.0.0"):
        self.tcp_address = tcp_address
        self.udp_address = udp_address
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.tcp_socket.bind((self.tcp_address, 9000))
        self.udp_socket.bind((self.udp_address, 9001))
        self.clients = {}
        self.rooms = {}
        self.TIMEOUT = 60

    def start(self):
        thread_handle_tcp = threading.Thread(target=self.wait_to_tcp_connections, daemon=True)
        thread_handle_tcp.start()

        # TODO: UDP通信や他の要件はissue毎にコメント外していく
        # thread_check_timeout = threading.Thread(target=self.check_client_timeout, daemon=True)
        # thread_check_timeout.start()
        # thread_receive_message = threading.Thread(target=self.receive_message, daemon=True)
        # thread_receive_message.start()


    def wait_to_tcp_connections(self):
        self.tcp_socket.listen(1)
        while True:
            print('\nwaiting to receive tcp connect')
            client_socket, addr = self.tcp_socket.accept()
            thread = threading.Thread(target=self.establish_tcp_connect, args=(client_socket, addr,))
            thread.start()

    def establish_tcp_connect(self, client_socket, addr):
        try:
            room_name, user_name, operation, state, payload = self.receive_tcp_message(client_socket)

            print("-------- receive request value   -----------")
            print("Room Name:", room_name)
            print("User Name:", user_name)
            print("Operation:", operation)
            print("State:", state)
            print("Payload:", payload)
            print("-------- receive request value end ---------")

            user = self.create_user(user_name, addr, operation)

            # stateを処理中に更新
            state =  1
            operation_response = {}
            if operation == Operation.CREATE_ROOM.value:
                operation_response = self.create_room(user, room_name)
            elif operation == Operation.JOIN_ROOM.value:
                operation_response = self.join_room(user, room_name)

            # 状態を更新
            if operation_response["status"] in [200, 201]:
                state = 2

            # TCPレスポンスを返す
            self.send_tcp_response(client_socket, operation, state, operation_response, room_name, user.token)


        except Exception as e:
            print("Error in receive_tcp_message:", e)

    def send_tcp_response(self, client_socket, operation, state, operation_response, room_name, token = None):
        """クライアントにレスポンスを送信する"""
        try:
            payload = {
                "status": operation_response["status"],
                "message": operation_response["message"],
                "token": token
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

    def receive_message(self):
        try:
            while True:
                print('\nwaiting to receive message')
                # データの取得（データを受け取るまで処理は止まる）
                data, address = self.udp_socket.recvfrom(4096)

                # 取得データを適切に処理
                username_len = int.from_bytes(data[:1], byteorder='big')
                username = data[1:1 + username_len].decode('utf-8')
                message_for_send = f"{username}: {data[1 + username_len:].decode('utf-8')}"

                # サーバーに参加しているクライアントを管理
                self.clients[address] = {'username':username,'last_time': time.time()}

                # 接続されている全てのクライアントにメッセージを送信
                self.broadcast(message_for_send.encode('utf-8'), address)

        finally:
            print('tcp socket closing....')
            self.tcp_socket.close()

    def create_room(self, user, room_name):
        if self.rooms.get(room_name) is None:
            chat_room = ChatRoom(room_name)
            chat_room.add_user(user)
            self.rooms[room_name] = chat_room

            return {"status": 200, "message": "Chat room created successfully."}
        else:
            return {"status": 400, "message": "Chat room already exists."}

    def create_user(self, user_name, address, operation):
        return User(
            user_name,
            address,
            self.generate_token(),
            MemberType.HOST.value if operation == Operation.CREATE_ROOM.value else MemberType.GUEST.value
        )

    def join_room(self, user, room_name):
        if self.rooms.get(room_name) is not None:
            self.rooms[room_name].add_user(user)
            return {"status": 200, "message": "Joined chat room successfully."}
        else:
            return {"status": 404, "message": "Chat room not found."}

    def broadcast(self, message:bytes, self_address=None):
        for address in self.clients:
            if (self_address == address):
                # クライアントが自分自身で送信したメッセージは本人には返さない。
                pass
            else:
                self.udp_socket.sendto(message, address)

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
            self.udp_socket.close()

    def shutdown(self):
        print("Server is shutting down.")
        self.udp_socket.close()
        # その他のクリーンアップ処理があればここに追加

if __name__ == "__main__":
    server = Server("0.0.0.0", "0.0.0.0")
    server.start()
    try:
        while True:  # メインスレッドをアクティブに保つ
            time.sleep(1)
    except KeyboardInterrupt:
        server.shutdown()
