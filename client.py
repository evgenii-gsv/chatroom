import socket
import threading
import sys

HOST = '127.0.0.1'
PORT = 5678

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client.connect((HOST, PORT))
except:
    print('Could not connect to the server. Check if server is running.')
    input()
    sys.exit()

def send_messages():
    while True:
        message = input()
        client.send(message.encode('utf-8'))

def receive_messages():
    while True:
        response = client.recv(2048).decode()
        if response == 'EXIT_PROGRAM':
            print('Connection closed, you can close the program.')
            break
        elif response == 'KICKED_BY_ADMIN':
            client.send('/leave_silently'.encode('utf-8'))
        else:
            print(response)

send_messages_thread = threading.Thread(target=send_messages)
receive_messages_thread = threading.Thread(target=receive_messages)
send_messages_thread.start()
receive_messages_thread.start()
