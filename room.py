import datetime

class Room:
    def __init__(self, name, creator):
        self.name = name
        self.admins = [creator]
        self.users = [creator]
        self.broadcast(f'{creator.nickname} joined the room {self.name}. Type /help for the list of commands.')
    
    def broadcast(self, message):
        current_time = datetime.datetime.now()
        current_time = f'{current_time.hour}:{current_time.minute:02d}:{current_time.second:02d}'
        message = f'{current_time} SERVER: ' + message
        for user in self.users:
            user.socket.send(message.encode('utf-8'))

    def send_message(self, message, sender):
        current_time = datetime.datetime.now()
        current_time = f'{current_time.hour}:{current_time.minute:02d}:{current_time.second:02d}'
        message = f'{current_time} {sender.nickname}: ' + message
        for user in self.users:
            if user != sender:
                user.socket.send(message.encode('utf-8'))
        
    def add_user(self, user):
        self.users.append(user)
        self.broadcast(f'{user.nickname} joined the room {self.name}. Type /help for the list of commands.')

    def remove_user(self, user):
        self.users.remove(user)
        self.broadcast(f'{user.nickname} left the room.')

    def remove_user_silently(self, user):
        self.users.remove(user)
