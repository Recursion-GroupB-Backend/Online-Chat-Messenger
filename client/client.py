import socket
import threading
import sys

def listen_for_messages(sock, username):
    while True:
        message, _ = sock.recvfrom(4096)
        print("\r" + message.decode('utf-8'))
        print(f"{username}> ", end="", flush=True)

def start_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ('127.0.0.1', 5000)

    username = input("Enter your username: ")
    username_bytes = username.encode('utf-8')
    if len(username_bytes) > 255:
        raise ValueError("Username too long (max 255 bytes)")

    # サーバーに初期メッセージ（ユーザー名のみ）を送信してアドレスを知らせる
    init_message = len(username_bytes).to_bytes(1, 'big') + username_bytes
    client_socket.sendto(init_message, server_address)

    threading.Thread(target=listen_for_messages, args=(client_socket, username), daemon=True).start()

    while True:
        try:
            message = input(f"{username}> ")
            full_message = len(username_bytes).to_bytes(1, 'big') + username_bytes + message.encode('utf-8')
            client_socket.sendto(full_message, server_address)
        except socket.error as e:
            print(f"Socket error: {e}")
            client_socket.close()
            break


if __name__ == "__main__":
    start_client()
