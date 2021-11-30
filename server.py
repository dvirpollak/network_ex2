import os
import socket

import sys
import time

import string
import random


def id_generator(size=128, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def make_dir(user_id):
    path = os.path.join(os.getcwd(), user_id)
    print(path)
    try:
        os.mkdir(path)
    except OSError:
        print("Creation of the directory %s failed" % path)
    else:
        print("Successfully created the directory %s " % path)

def clear_folder(dir):
    if os.path.exists(dir):
        for the_file in os.listdir(dir):
            file_path = os.path.join(dir, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                else:
                    clear_folder(file_path)
                    os.rmdir(file_path)
            except Exception as e:
                print(e)
    os.rmdir(dir)

def accept_tex(path):
    server.listen(6)
    # c, a = s.accept()

    file_name = path.split("/")[-1]
    filetodown = open(path, "wb")
    while True:
        print("Receiving....")
        data = client_socket.recv(1024)
        if data == b"DONE":
            print("Done Receiving.")
            break
        filetodown.write(data)
    filetodown.close()
    client_socket.send(bytes("Thank you for connecting.", "utf-8"))
    # client_socket.shutdown(2)
    # client_socket.close()
    # server.close()


user_dict = []
user_id_connected = " "
port = int(sys.argv[1])
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', port))
server.listen(5)


while True:
    client_socket, client_address = server.accept()
    print('Connection from: ', client_address)
    data = client_socket.recv(1024)
    message_in_str = str(data, 'utf-8')
    print(message_in_str)
    message_list = message_in_str.split('$')
    if message_list[0] == 'Hi':
        generate = id_generator()
        # user_dict.setdefault(generate, message_list[1])
        user_dict.append(generate)
        user_id_connected = generate
        make_dir(generate)
        client_socket.send(bytes(generate, 'utf-8'))
    if message_list[0] == 'cr':

        completeName = os.path.join(os.getcwd(), message_list[2].replace(".", user_id_connected))
        print(completeName)
        accept_tex(message_list[2].replace(".", user_id_connected))
        #os.replace(os.path.join(os.getcwd(),file_name), os.path.join(os.getcwd(), message_list[2].replace(".", user_id_connected)))
    if message_list[0] == 'crf':
        spilt_folder_file = message_list[2].split(".")
        make_dir(message_list[1]+"/"+spilt_folder_file[1])
    if message_list[0] == 'del':
        spilt_folder_file = message_list[2].split(".")
        clear_folder(message_list[1] + spilt_folder_file[1])




    # if not data or message_in_str == "FIN":
    #     client_socket.send(bytes("FIN", "utf_8"))
    #     break

client_socket.close()
print('Client disconnected')
