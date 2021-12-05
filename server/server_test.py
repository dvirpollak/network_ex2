import os
import socket

import sys
import time

import string
import random

TOKEN_IN_BYTES = b"$"
TOKEN_STR = "$"
REC_ACK = sys.getsizeof(b"ACK")
PORT = int(sys.argv[1])
linox_token = "/"
FORMAT = "utf-8"
SERVER_DATA_PATH = os.getcwd()

#--------------------------------
#
def return_path(root, identifier):
    root_list = root.split("/")
    i = root_list.index(identifier)
    path = ''
    for x in root_list[i + 1:]:
        path += "/"
        path += x
    return path


# ---------------------------
# make_data - will take a list and
# make the data to send even encode(FORMAT)
def make_data(all_data):
    full_data = ""

    for data in all_data:
        full_data += data + TOKEN_STR
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

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', PORT))
    server.listen(5)
    print(f"[LISTENING] Server is listening on {PORT}.")
    size = 1024
    while True:
        client, addr = server.accept()
        print(f"[NEW CONNECTION] {addr} connected.")

        while True:
            data = client.recv(size)
            data = data.split(TOKEN_IN_BYTES)
            cmd = data[0]
            # to set the size of the commend
            if cmd == b"SET_SIZE":
                size = int(data[1].decode(FORMAT))
                print("SIZE of next pact =" + str(size))
                break
            # new user is connecting
            if cmd == b"NEW_USER":
                identifier = id_generator()
                user_comp_id_connected = data[1].decode(FORMAT)
                make_dir(identifier)
                send_data = make_data(["NEW_USER_ID", identifier])
                client.send(send_data)
                print("new user identifier = " + identifier)
                break

            # user with a user name connect will receive al the data contain in the file
            if cmd == b"CONNECT":
                identifier = data[2].decode(FORMAT)
                user_comp_id_connected = data[1].decode(FORMAT)
                path = os.path.join(os.getcwd(), identifier)
                for root, dirs, files in os.walk(path, topdown=True):

                    for name in files:
                        full_path = os.path.join(root, name)
                        deliver_path = return_path(full_path, identifier)
                        size_of_next_data = sys.getsizeof(make_data(['UPLOAD_FILE', deliver_path]))
                        client.send(make_data(['SET_SIZE', str(size_of_next_data)]))

                        print(name)
                        file_size = os.path.getsize(full_path)
                        client.recv(REC_ACK)
                        client.send(make_data(['UPLOAD_FILE', deliver_path[1:], str(file_size)]))
                        print(make_data(['UPLOAD_FILE', deliver_path[1:], str(file_size)]))
                        client.recv(REC_ACK)

                        file_to_send = open(full_path, "rb")

                        data = file_to_send.read()
                        client.send(data)

                        file_to_send.close()
                        client.recv(REC_ACK)
                        print("done sending file name" + name)

                    for name in dirs:
                        full_path = os.path.join(root, name)
                        deliver_path = return_path(full_path, identifier)
                        size_of_next_data = sys.getsizeof(make_data(['CRF', deliver_path]))
                        client.send(make_data(['SET_SIZE', str(size_of_next_data)]))
                        client.recv(REC_ACK)

                        client.send(make_data(['CRF', deliver_path[1:]]))
                        client.recv(REC_ACK)
                        print("send client to create dir-" + name)
                # sending the client
                client.send(b"DONE")
                print("done sending to client" + identifier + "update")
                break

            # makes a dir
            elif cmd == b'CRF':
                make_dir(identifier + data[1].decode(FORMAT))
                break

            # uplod file
            elif cmd == b"UPLOAD":

                path_to_put = data[1].decode(FORMAT)[1:]
                filepath = os.path.join(SERVER_DATA_PATH, identifier,
                                        path_to_put)  # we need to check after change

                # right to the file the content that it receive
                file_to_down = open(filepath, "wb")
                len_of_data_rec = client.recv(1024)
                while len_of_data_rec:
                    file_to_down.write(len_of_data_rec)
                    len_of_data_rec = client.recv(1024)
                file_to_down.close()

                print("Done Receiving the file. " + filepath)
                file_to_down.close()
                break
            # delete the file
            elif cmd == b"DELETE":
                event_path_del = data[1].decode(FORMAT)[1:]
                path_del = os.path.join(SERVER_DATA_PATH, identifier, event_path_del)  # check after change
                # if its a file it will delete the file
                if os.path.isfile(path_del):
                    os.unlink(path_del)

                else:  # if it a dir it will delete the dir
                    clear_folder(path_del)
                print("DELETE-" + path_del)
                break
            # move file from source_path to destination_path
            elif cmd == b"MOVE":
                source_path = os.path.join(SERVER_DATA_PATH, identifier, data[1].decode(FORMAT))
                destination_path = os.path.join(SERVER_DATA_PATH, identifier, data[2].decode(FORMAT))
                os.replace(source_path, destination_path)
                print("file moved from- " + source_path + "to" + destination_path)

        print(f"[DISCONNECTED] {addr} disconnected")
        client.close()


if __name__ == "__main__":
    main()
