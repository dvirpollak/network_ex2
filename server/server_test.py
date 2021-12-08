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
FORMAT = "utf-8"
SERVER_DATA_PATH = os.getcwd()
DATA_BASE = {}


# --------------------------------
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
                pass
               # print(e)
    os.rmdir(dir)


def sending_updates(list_of_updates, client):
    while len(list_of_updates):

        full_data = list_of_updates.pop(0)

        client.send(make_data(["SET_SIZE", str(sys.getsizeof(full_data))]))

        data = full_data.split(b"$")
        cmd = data[0]

        if cmd == b"DELETE":
            client.send(full_data)
            client.recv(REC_ACK)

        # Receiving files from server
        if cmd == b'UPLOAD':
            file_to_send = ''
            try:
                file_to_send = open(os.path.join(SERVER_DATA_PATH, data[1].decode(FORMAT)[1:]), "rb")
                print("we are in try")
            except OSError:
                print("we are Eror")
                continue

            client.send(full_data)
            client.recv(REC_ACK)


            data = file_to_send.read()
            client.send(data)
            file_to_send.close()

            client.recv(REC_ACK)
            continue
        # Creating dictionaries
        if cmd == b'CRF':
            client.send(full_data)
            print(client)
            client.recv(REC_ACK)
            continue
        if cmd == b'MOVE':
            client.send(full_data)
            client.recv(REC_ACK)
            continue
        if cmd == b'RENAME_DIR':
            client.send(full_data)
            client.recv(REC_ACK)
            continue

    client.send(b"NO_UPDATES")
    return


def main():
    print("[STARTING] Server is starting")
    identifier = ""
    computer_id = ""

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', PORT))
    server.listen(5)
    print(f"[LISTENING] Server is listening on {PORT}.")

    while True:
        size = 1024

        client, addr = server.accept()
        print(f"[NEW CONNECTION] {addr} connected.")

        while True:

            full_data = client.recv(size)
            data = full_data.split(TOKEN_IN_BYTES)
            cmd = data[0]
            # to set the size of the commend
            if cmd == b"SET_SIZE":
                size = int(data[1].decode(FORMAT))
                identifier = data[2].decode(FORMAT)
                try:
                    computer_id = data[3].decode(FORMAT)
                except IndexError:
                    pass
                client.send(b"ACK")
                continue
            if cmd == b"CHECK_FOR_UPDATE":
                computer_id = data[1].decode(FORMAT)
                if not DATA_BASE[identifier][computer_id]:
                    print("NO_UPDATES for " + computer_id)
                    client.send(b"NO_UPDATES")
                    break
                print("there is UPDATES for " + computer_id)
                sending_updates(DATA_BASE.get(identifier).get(computer_id), client)
                break

            # new user is connecting
            if cmd == b"NEW_USER":
                identifier = id_generator()

                computer_id = data[1].decode(FORMAT)
                DATA_BASE.setdefault(identifier, {computer_id: []})
                make_dir(identifier)

                client.send(identifier.encode(FORMAT))
                continue

            # user with a user name connect will receive al the data contain in the file
            if cmd == b"CONNECT":
                identifier = data[2].decode(FORMAT)
                computer_id = data[1].decode(FORMAT)
                if computer_id in DATA_BASE[identifier].keys():
                   # print("you connected befor")
                    list_of_updates = DATA_BASE.get(identifier).get(computer_id)
                    sending_updates(list_of_updates, client)

                else:
                    # add to data base

                    DATA_BASE.get(identifier).update({computer_id: []})
                    path = os.path.join(os.getcwd(), identifier)
                    for root, dirs, files in os.walk(path, topdown=True):

                        for name in files:
                            full_path = os.path.join(root, name)
                            deliver_path = return_path(full_path, identifier)
                            size_of_next_data = sys.getsizeof(make_data(['UPLOAD_FILE', deliver_path]))
                            client.send(make_data(['SET_SIZE', str(size_of_next_data)]))

                            #print(name)
                            file_size = os.path.getsize(full_path)
                            client.recv(REC_ACK)
                            client.send(make_data(['UPLOAD_FILE', deliver_path[1:], str(file_size)]))
                            #print(make_data(['UPLOAD_FILE', deliver_path[1:], str(file_size)]))
                            client.recv(REC_ACK)

                            file_to_send = open(full_path, "rb")

                            data = file_to_send.read()
                            client.send(data)

                            file_to_send.close()
                            client.recv(REC_ACK)
                            #print("done sending file name" + name)

                        for name in dirs:
                            full_path = os.path.join(root, name)
                            deliver_path = return_path(full_path, identifier)
                            size_of_next_data = sys.getsizeof(make_data(['CRF', deliver_path]))
                            client.send(make_data(['SET_SIZE', str(size_of_next_data)]))
                            client.recv(REC_ACK)

                            client.send(make_data(['CRF', deliver_path[1:]]))
                            client.recv(REC_ACK)
                           # print("send client to create dir-" + name)
                    # sending the client
                    client.send(b"DONE")
                   # print("done sending to client" + identifier + "update")
                break

            # makes a dir
            elif cmd == b'CRF':
                for comp, updates in DATA_BASE.get(identifier).items():
                    if comp == computer_id:
                        continue
                    updates.append(full_data)
                make_dir(identifier + data[1].decode(FORMAT))
                client.send(b'ACK')
                continue

            # uplod file
            elif cmd == b"UPLOAD":

                path_to_put = data[1].decode(FORMAT)[1:]
                filepath = os.path.join(SERVER_DATA_PATH, identifier,
                                        path_to_put)  # we need to check after change
                for comp, updates in DATA_BASE.get(identifier).items():
                    if comp == computer_id:
                        continue
                    updates.append(full_data)

                # right to the file the content that it receive
                file_to_down = open(filepath, "wb")
                size_file = int(data[2].decode(FORMAT))
                client.send(b'ACK')
                file_receive = client.recv(size_file)
                counter_bytes = 0
                while file_receive:
                    file_to_down.write(file_receive)
                    counter_bytes += len(file_receive)
                    if counter_bytes == size_file:
                        break
                    file_receive = client.recv(1024)
                file_to_down.close()
                client.send(b'ACK')
                continue
            # delete the file
            elif cmd == b"DELETE":
                event_path_del = data[1].decode(FORMAT)[1:]
                path_del = os.path.join(SERVER_DATA_PATH, identifier, event_path_del)  # check after change
                if os.path.isfile(path_del):
                    os.unlink(path_del)

                else:  # if it a dir it will delete the dir
                    clear_folder(path_del)
                #print("DELETE-" + path_del)
                # updat the changes in the all the computer
                for key, item in DATA_BASE.get(identifier).items():
                    if key == computer_id:
                        continue
                    item.append(full_data)
                client.send(b"ACK")
                continue
            # move file from source_path to destination_path
            elif cmd == b"MOVE":
                source_path = os.path.join(SERVER_DATA_PATH, identifier, data[1].decode(FORMAT)[1:])
                destination_path = os.path.join(SERVER_DATA_PATH, identifier, data[2].decode(FORMAT)[1:])
                if os.path.exists(destination_path):
                    client.send(b'ACK')
                    continue
                # updat the changes in the all the computer
                for key, item in DATA_BASE.get(identifier).items():
                    if key == computer_id:
                        continue
                    item.append(full_data)
                if not os.path.exists(source_path):
                    #print("there is no path - " + source_path)
                    continue
                os.replace(source_path, destination_path)
                client.send(b'ACK')
                #print("file moved from- " + source_path + " to " + destination_path)
                continue
            elif cmd == b"RENAME_DIR":
                source_path = os.path.join(SERVER_DATA_PATH, identifier, data[1].decode(FORMAT)[1:])
                destination_path = os.path.join(SERVER_DATA_PATH, identifier, data[2].decode(FORMAT)[1:])
                # updat the changes in the all the computer
                for key, item in DATA_BASE.get(identifier).items():
                    if key == computer_id:
                        continue
                    item.append(full_data)
                os.rename(source_path, destination_path)
                # print("file rename from- " + source_path + " to " + destination_path)
                client.send(b'ACK')
                continue
            elif cmd == b"SYN":

                break

        print(f"[DISCONNECTED] {addr} disconnected")
        client.close()
        print("*********************************************************\n")
        for key, item in DATA_BASE.items():
            print(key, item)
        print("\n******************************************************************")

if __name__ == "__main__":
    main()
