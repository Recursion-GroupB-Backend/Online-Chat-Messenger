import socket
import time

class User:
    def __init__(self, user_name, tcp_address, udp_address, token, member_type, public_key):
        self.user_name = user_name
        self.tcp_address = tcp_address
        self.udp_address = udp_address
        self.token = token
        self.last_active = time.time()
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.member_type = member_type
        self.public_key = public_key

    # def send_message(self):
