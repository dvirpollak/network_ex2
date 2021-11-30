import os
import socket

import sys
import time

from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler

import string
import random


def id_generator(size=128, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def open_directory(generate):
    path = os.getcwd() + "/" + generate + "/"
    print(path)
    try:
        os.mkdir(path)
    except OSError:
        print("Creation of the directory %s failed" % path)
    else:
        print("Successfully created the directory %s " % path)


def accept_tex():
    # s.listen(1)
    # c, a = s.accept()
    filetodown = open("code", "wb")
    while True:
        print("Receiving....")
        data = client_socket.recv(1024)
        if data == b"DONE":
            print("Done Receiving.")
            break
        filetodown.write(data)
    filetodown.close()
    client_socket.send(bytes("Thank you for connecting.", "utf-8"))
    client_socket.shutdown(2)
    client_socket.close()
    server.close()


user_dict = {}
port = int(sys.argv[1])
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', port))
server.listen(5)
client_socket, client_address = server.accept()
print('Connection from: ', client_address)

while True:

    data = client_socket.recv(100)
    message_in_str = str(data, 'utf-8')
    print(message_in_str)
    message_list = message_in_str.split('$')
    if message_list[0] == 'Hi':
        generate = id_generator()
        user_dict.setdefault(generate, message_list[1])
        open_directory(generate)
        client_socket.send(bytes(generate, 'utf-8'))

    # if not data or message_in_str == "FIN":
    #     client_socket.send(bytes("FIN", "utf_8"))
    #     break

client_socket.close()
print('Client disconnected')
