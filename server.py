import socket
import threading
from time import sleep
from room import Room
from user import User

HOST = '127.0.0.1'
PORT = 5678

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()
print('Server started')

rooms = {}
occupied_nicks = []
chat_commands = {
    '/help': 'Shows all available commands.',
    '/list': 'Shows all users in this chatroom.',
    '/leave': 'Leave this chatroom.',
    '/make_admin': 'ADMINS ONLY, follow this command by the nickname of a person you want to make an admin.',
    '/kick': 'ADMINS ONLY, kick the person from the chatroom, follow this command by the nickname of a person.',
    '/close': 'ADMINS ONLY, close this chatroom.'
}

def execute_command(command, user, room_name):
    if command.lower().strip().startswith('/help'):
        commands_list = 'The list of commands:\n'
        for key, value in chat_commands.items():
            commands_list += f'{key} - {value}\n'
        user.socket.send(commands_list.encode('utf-8'))
    
    elif command.lower().strip().startswith('/list'):
        user_list = 'The list of users in this chatroom:\n'
        for chatter in rooms[room_name].users:
            if chatter in rooms[room_name].admins:
                user_list += f'{chatter.nickname} (ADMIN)\n'
            else:
                user_list += f'{chatter.nickname}\n'
        user.socket.send(user_list.encode('utf-8'))
    
    elif command.lower().strip().startswith('/leave'):
        rooms[room_name].remove_user(user)
        if rooms[room_name].users == []:
            rooms.pop(room_name)

    elif command.lower().strip().startswith('/leave_silently'):
        rooms[room_name].remove_user_silently(user)
        if rooms[room_name].users == []:
            rooms.pop(room_name)
    
    elif command.lower().strip().startswith('/make_admin'):
        nickname = command[12:]
        if user not in rooms[room_name].admins:
            user.socket.send('You need to be admin to make admins.'.encode('utf-8'))
        elif nickname == '':
            user.socket.send('Type nickname after the command.'.encode('utf-8'))
        elif nickname in [x.nickname for x in rooms[room_name].users]:
            for chatter in rooms[room_name].users:
                if chatter.nickname == nickname:
                    rooms[room_name].admins.append(chatter)
                    rooms[room_name].broadcast(f'{nickname} was made admin by {user.nickname}.')
        else:
            user.socket.send(f'User {nickname} not found.'.encode('utf-8'))
    
    elif command.lower().strip().startswith('/kick'):
        nickname = command[6:]
        if user not in rooms[room_name].admins:
            user.socket.send('You need to be admin to kick users.'.encode('utf-8'))
        elif nickname == '':
            user.socket.send('Type nickname after the command.'.encode('utf-8'))
        elif nickname in [x.nickname for x in rooms[room_name].users]:
            for chatter in rooms[room_name].users:
                if chatter.nickname == nickname:
                    rooms[room_name].broadcast(f'{nickname} was kicked by {user.nickname}.')
                    sleep(1)
                    chatter.socket.send('KICKED_BY_ADMIN'.encode('utf-8'))               
        else:
            user.socket.send(f'User {nickname} not found.'.encode('utf-8'))
    
    elif command.lower().strip().startswith('/close'):
        if user not in rooms[room_name].admins:
            user.socket.send('You need to be admin to close chatroom.'.encode('utf-8'))
        else:   
            rooms[room_name].broadcast(f'This chatroom is closed by {user.nickname}.')
            sleep(1)
            for chatter in rooms[room_name].users:
                chatter.socket.send('KICKED_BY_ADMIN'.encode('utf-8'))
                
    else:
        user.socket.send('Unknown command. Type /help for the list of commands.'.encode('utf-8'))
           
def close_connection(user):
    try:
        occupied_nicks.remove(user.nickname)
        user.socket.close()
        print(f'{user.nickname} lost connection.')
    except:
        pass

def lobby(user):
    validating_nickname = True
    while validating_nickname:
        try:
            user.socket.send('Send your nickname.'.encode('utf-8'))
            nickname = user.socket.recv(2048).decode('utf-8')
            if nickname not in occupied_nicks:
                user.nickname = nickname
                occupied_nicks.append(nickname)
                validating_nickname = False
            else:
                user.socket.send('This nickname is occupied, please try again.'.encode('utf-8'))
                sleep(1)
        except:
            user.socket.close()

    main_menu = f'''
Welcome to the Eugene's chatroom, {user.nickname}. What do you want to do?

(C)reate room
(J)oin room
(E)xit
'''
    #running main menu until user disconnects
    while True:
        try:
            user.socket.send(main_menu.encode('utf-8'))
            response = user.socket.recv(2048).decode('utf-8')
            if response.lower().strip() in ['e', 'exit']:
                user.socket.send('EXIT_PROGRAM'.encode('utf-8'))
                break
            # creating new room
            elif response.lower().strip() in ['c', 'create', 'create room']:
                while True:
                    try:
                        user.socket.send('Choose the name of your room.'.encode('utf-8'))
                        room_name = user.socket.recv(2048).decode('utf-8')
                        if room_name not in rooms:
                            rooms[room_name] = Room(room_name, user)
                            # start chatting
                            while True:
                                message = user.socket.recv(2048).decode('utf-8')
                                if not message:
                                    rooms[room_name].remove_user(user)
                                    if rooms[room_name].users == []:
                                        rooms.pop(room_name)
                                        break
                                elif message.startswith('/'):
                                    execute_command(message, user, room_name)
                                    if message.lower().strip().startswith('/leave'):
                                        break
                                else:
                                    rooms[room_name].send_message(message, user)
                            break    
                        else:
                            user.socket.send(f'The room with the name {room_name} already exists, please try again.'.encode('utf-8'))
                            sleep(1)
                            break
                    except: 
                        break
            
            # joining existing room
            elif response.lower().strip() in ['j', 'join', 'join room']:
                if rooms != {}:
                    while True:
                        available_rooms = '''
Send the number of the room that you want to join.
'''
                        i = 1
                        rooms_list = list(rooms)
                        for room in rooms_list:
                            available_rooms += f'{i}: {room}\n'
                            i += 1
                        user.socket.send(available_rooms.encode('utf-8'))
                        room_number = user.socket.recv(2048).decode('utf-8')
                        try:
                            room_number = int(room_number)
                            room_name = rooms_list[room_number-1]
                            rooms[room_name].add_user(user)
                            # start chatting
                            while True:
                                message = user.socket.recv(2048).decode('utf-8')
                                if not message:
                                    rooms[room_name].remove_user(user)
                                    if rooms[room_name].users == []:
                                        rooms.pop(room_name)
                                        break
                                elif message.startswith('/'):
                                    execute_command(message, user, room_name)
                                    if message.lower().strip().startswith('/leave'):
                                        break
                                else:
                                    rooms[room_name].send_message(message, user)
                            break
                        except:
                            user.socket.send('No such room found, please try again.'.encode('utf-8'))
                            sleep(1)
                            break
                else:
                    user.socket.send('No rooms available, please create a new one.'.encode('utf-8'))
                    sleep(1)
            else:
                user.socket.send('The choice is not clear, please try again.'.encode('utf-8'))
                sleep(1)
        except:
            close_connection(user)
    close_connection(user)

# accepting all incoming connections
def receive():
    while True:
        client, ip = server.accept()
        user = User(client, ip)
        print(f'Connected with {user.ip_address}')
        lobby_thread = threading.Thread(target=lobby, args=(user,))
        lobby_thread.start()

if __name__ == '__main__':
    receive()