import socket
import time

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('127.0.0.1', 5000))
    print("UDP server listening on 127.0.0.1:5000")

    clients = {}

    while True:
        try:
            print("data")
            data, client_address = server_socket.recvfrom(4096)

            username_length = data[0]
            username = data[1:1+username_length].decode('utf-8')
            message = data[1+username_length:].decode('utf-8')

            formatted_message = f"{username}> {message}".encode('utf-8')
            print(f"Message from {username}: {message}")

            clients[client_address] = time.time()

            for client in list(clients.keys()):
                if client != client_address:
                    server_socket.sendto(formatted_message, client)

            current_time = time.time()
            for client in list(clients.keys()):
                if current_time - clients[client] > 60:
                    del clients[client]
        except socket.error as e:
            print(f"Socket error: {e}")
            server_socket.close()

if __name__ == "__main__":
    start_server()
