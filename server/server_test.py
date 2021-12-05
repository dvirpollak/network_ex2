import os
import socket

import sys
import time

import string
import random

PORT = int(sys.argv[1])

FORMAT = "utf-8"
SERVER_DATA_PATH = os.getcwd()


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


# -------------------
# clear_folder will delete all the content of the folder

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


def main():
    print("[STARTING] Server is starting")
    user_id_connected = ""
    user_comp_id_connected = ""

    token = "$"
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', PORT))
    server.listen(5)
    print(f"[LISTENING] Server is listening on {PORT}.")
    size = 1024
    while True:
        conn, addr = server.accept()
        print(f"[NEW CONNECTION] {addr} connected.")

        while True:
            data = conn.recv(size)
            data = data.split(b"$")
            cmd = data[0]
            # to set the size of the commend
            if cmd == b"SET_SIZE":
                size = int(data[1].decode(FORMAT))
                print(size)
                break
            # new user is connecting
            if cmd == b"NEW_USER":
                generate = id_generator()
                user_id_connected = generate
                user_comp_id_connected = data[1].decode(FORMAT)
                make_dir(generate)
                send_data = "NEW_USER_ID" + token + generate
                conn.send(send_data.encode(FORMAT))
                break

            # user with a user name concect
            if cmd == b"CONNECT":
                user_id_connected = data[2].decode(FORMAT)
                user_comp_id_connected = data[1].decode(FORMAT)
                make_dir(user_id_connected)
                break

            # makes a dir
            elif cmd == b'CRF':
                make_dir(user_id_connected + data[1].decode(FORMAT))
                break

            # uplod file
            elif cmd == b"UPLOAD":

                path_to_put = data[1].decode(FORMAT)
                print(path_to_put)
                filepath = SERVER_DATA_PATH + "/" + user_id_connected + path_to_put
                print(filepath)
                # right to the file the content that it receive
                filetodown = open(filepath, "wb")
                while data:
                    print("Receiving....")
                    data = conn.recv(1024)
                    filetodown.write(data)
                print("Done Receiving.")
                filetodown.close()
                break
            # delete the file
            elif cmd == b"DELETE":
                event_path_del = data[1].decode(FORMAT)
                path_del = SERVER_DATA_PATH + "/" + user_id_connected + event_path_del
                # if its a file
                if os.path.isfile(path_del):
                    os.unlink(path_del)

                else:
                    clear_folder(path_del)
                print(path_del + "-DELETE")
                break

        print(f"[DISCONNECTED] {addr} disconnected")
        conn.close()


if __name__ == "__main__":
    main()
