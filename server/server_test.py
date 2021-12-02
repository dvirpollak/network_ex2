import os
import socket

import sys
import time

import string
import random

PORT = int(sys.argv[1])
SIZE = 1024
FORMAT = "utf-8"
SERVER_DATA_PATH = "server_data"


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


def main():
    print("[STARTING] Server is starting")
    user_id_connected = ""
    user_comp_id_connected = ""

    token = "$"
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', PORT))
    server.listen(5)
    print(f"[LISTENING] Server is listening on {PORT}.")

    while True:
        conn, addr = server.accept()
        print(f"[NEW CONNECTION] {addr} connected.")

        while True:
            data = conn.recv(SIZE)
            data = data.split(b"$")
            cmd = data[0]
            print(data)
            if cmd == b"NEW_USER":
                generate = id_generator()
                user_id_connected = generate
                user_comp_id_connected = data[1].decode(FORMAT)
                make_dir(generate)
                send_data = "NEW_USER_ID" + token + generate
                conn.send(send_data.encode(FORMAT))
                break
            # a(["CONNECT", computer_id, identifier])
            if cmd == b"CONNECT":
                user_id_connected = data[2].decode(FORMAT)
                user_comp_id_connected = data[1].decode(FORMAT)
                make_dir(user_id_connected)
                break
            elif cmd == b'CRF':

                make_dir(os.path.join(user_id_connected,data[1].decode(FORMAT)))
                break



            elif cmd == b"UPLOAD":

                name, text = data[1], data[2]
                filepath = os.path.join(SERVER_DATA_PATH, name)
                with open(filepath, "wb") as f:
                    f.write(text)

                send_data = "OK@File uploaded successfully."
                conn.send(send_data.encode(FORMAT))

            elif cmd == b"DELETE":
                files = os.listdir(SERVER_DATA_PATH)
                send_data = "OK@"
                filename = data[1]

                if len(files) == 0:
                    send_data += "The server directory is empty"
                else:
                    if filename in files:
                        os.system(f"rm {SERVER_DATA_PATH}/{filename}")
                        send_data += "File deleted successfully."
                    else:
                        send_data += "File not found."

                conn.send(send_data.encode(FORMAT))

        print(f"[DISCONNECTED] {addr} disconnected")
        conn.close()


if __name__ == "__main__":
    main()
