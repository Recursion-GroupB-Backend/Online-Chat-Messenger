import socket
import time

class User:
    def __init__(self, user_name, address, udp_address, token, member_type):
        self.user_name = user_name
        self.address = address
        self.udp_address = udp_address
        self.token = token
        self.last_active = time.time()
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.member_type = member_type

    # def send_message(self):
