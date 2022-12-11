class User:
    def __init__(self, socket, ip_address):
        self.socket = socket
        self.ip_address = ip_address
        self.nickname = ''