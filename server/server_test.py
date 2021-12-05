import os
import socket

import sys
import time

import string
import random

REC_ACK = 3
PORT = int(sys.argv[1])

FORMAT = "utf-8"
SERVER_DATA_PATH = os.getcwd()


def return_path(root, identifier):
    root_list = root.split("/")
    i = root_list.index(identifier)
    path = ''
    for x in root_list[i+1:]:
        path += "/"
        path += x
    return path

# ---------------------------
# make_data - will take a list and
# make the data to send even encode(FORMAT)
def make_data(all_data):
    full_data = ""
    token = "$"
    for data in all_data:
        full_data += data + token
    print(full_data)
    return full_data.encode(FORMAT)


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
    identifier = ""
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
                identifier = generate
                user_comp_id_connected = data[1].decode(FORMAT)
                make_dir(generate)
                send_data = "NEW_USER_ID" + token + generate
                conn.send(send_data.encode(FORMAT))
                break

            # user with a user name concect
            if cmd == b"CONNECT":
                identifier = data[2].decode(FORMAT)
                user_comp_id_connected = data[1].decode(FORMAT)
                path = os.path.join(os.getcwd(), identifier)
                for root, dirs, files in os.walk(path, topdown=True):


                    for name in files:
                        full_path = os.path.join(root,name)
                        deliver_path = return_path(full_path,identifier)
                        size_of_next_data = sys.getsizeof(make_data(['UPLOAD_FILE', deliver_path]))
                        conn.send(make_data(['SET_SIZE', str(size_of_next_data)]))

                        print(name)
                        file_size = os.path.getsize(full_path)
                        conn.recv(REC_ACK)
                        conn.send(make_data(['UPLOAD_FILE', deliver_path[1:], str(file_size)]))
                        print(make_data(['UPLOAD_FILE', deliver_path[1:], str(file_size)]))
                        conn.recv(REC_ACK)

                        file_to_send = open(full_path, "rb")


                        data = file_to_send.read()
                        conn.send(data)

                        file_to_send.close()
                        conn.recv(REC_ACK)
                        print("done sending")

                    for name in dirs:
                        full_path = os.path.join(root, name)
                        deliver_path = return_path(full_path, identifier)
                        size_of_next_data = sys.getsizeof(make_data(['CRF', deliver_path]))
                        conn.send(make_data(['SET_SIZE', str(size_of_next_data)]))
                        conn.recv(REC_ACK)
                        # time.sleep(0.1)
                        print(make_data(['CRF', deliver_path[1:]]))
                        conn.send(make_data(['CRF', deliver_path[1:]]))
                        conn.recv(REC_ACK)
                        print(name)

                make_dir(identifier)
                print(identifier)
                conn.send(b"DONE")
                print("don sending")
                break

            # makes a dir
            elif cmd == b'CRF':
                make_dir(identifier + data[1].decode(FORMAT))
                break

            # uplod file
            elif cmd == b"UPLOAD":

                path_to_put = data[1].decode(FORMAT)
                print(path_to_put)
                filepath = SERVER_DATA_PATH + "/" + identifier + path_to_put  #######there is "/" befor path_to_put
                print(filepath)
                # right to the file the content that it receive
                filetodown = open(filepath, "wb")
                l = conn.recv(1024)
                while (l):
                    print("Receiving...")

                    filetodown.write(l)
                    l = conn.recv(1024)
                filetodown.close()

                print("Done Receiving.")
                filetodown.close()
                break
            # delete the file
            elif cmd == b"DELETE":
                event_path_del = data[1].decode(FORMAT)
                path_del = SERVER_DATA_PATH + "/" + identifier + event_path_del
                # if its a file
                if os.path.isfile(path_del):
                    os.unlink(path_del)

                else:
                    clear_folder(path_del)
                print(path_del + "-DELETE")
                break
            elif cmd == b"MOVE":
                os.replace(os.path.join(SERVER_DATA_PATH, identifier, data[1].decode(FORMAT)),
                           os.path.join(SERVER_DATA_PATH, identifier, data[2].decode(FORMAT)))

        print(f"[DISCONNECTED] {addr} disconnected")
        conn.close()


if __name__ == "__main__":
    main()
