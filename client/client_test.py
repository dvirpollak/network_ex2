import socket
import sys
import os
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from watchdog.events import LoggingEventHandler
import random
import string

# Argument received from main
ADDR = (sys.argv[1], int(sys.argv[2]))
FORMAT = "utf-8"
SIZE = 1024
ClINET_PATH = sys.argv[3]
time_connect = int(sys.argv[4])
flag_rename_dir = False


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


# will do with a settimeout
def client_is_listening(computer_id):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
    client.send(make_data([b'CHECK_FOR_UPDATE', computer_id]))
    data = client.recv(1024)
    data = data.split(b'$')
    # number of command to run a loop
    cmd = data[0]
    while True:
        if cmd == b'GOOD':
            break
        if cmd == b'UPLOAD':
            path_to_put = data[1].decode(FORMAT)[1:]
            filepath = os.path.join(ClINET_PATH, path_to_put)  # we need to check after change

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

        if cmd == b'DELETE':
            event_path_del = data[1].decode(FORMAT)[1:]
            path_del = os.path.join(ClINET_PATH, event_path_del)  # check after change
            # if its a file it will delete the file
            if os.path.isfile(path_del):
                os.unlink(path_del)

            else:  # if it a dir it will delete the dir
                clear_folder(path_del)
            print("DELETE-" + path_del)
            break

        if cmd == b'MOVE':
            source_path = os.path.join(ClINET_PATH, data[1].decode(FORMAT))
            destination_path = os.path.join(ClINET_PATH, data[2].decode(FORMAT))
            os.replace(source_path, destination_path)
            print("file moved from- " + source_path + "to" + destination_path)
            break

        if cmd == b'CRF':
            make_dir(ClINET_PATH + data[1].decode(FORMAT))
            break

        if cmd == b"RENAME_DIR":
            source_path = os.path.join(ClINET_PATH, data[1].decode(FORMAT)[1:])
            destination_path = os.path.join(ClINET_PATH, data[2].decode(FORMAT)[1:])
            os.rename(source_path, destination_path)
            print("file rename from- " + source_path + " to " + destination_path)
            break

    client.close()



def is_file_in_dict(event, path):
    file_list = []

    for root, dirs, files in os.walk(path):
        for file in files:
            file_list.append(os.path.join(root, file))

    print(file_list)
    return event in file_list


# --------------------------
# return path
def return_path(root):
    parent_file = sys.argv[3].split("/")[-1]
    root_to_list = root.split("/")
    i = root_to_list.index(parent_file)
    path = ''
    for x in root_to_list[i+1:]:
        path += "/" + x
    return path


# --------------------------
# This function will help us import all files from server
# to the client folder, when logging with existing ID
def second_connection(identifier, computer_id):
    data = make_data(["CONNECT", computer_id, identifier])
    set_size(data)
    # connect to the server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
    client.send(data)
    size = 1024
    while True:
        data = client.recv(size)
        data = data.split(b"$")
        cmd = data[0]
        # adjusting size
        if cmd == b'SET_SIZE':
            size = int(data[1].decode(FORMAT))
            client.send(b'ACK')
            continue
        # Receiving files from server
        if cmd == b'UPLOAD_FILE':
            file_to_down = open(os.path.join(ClINET_PATH, data[1].decode(FORMAT)), "wb")
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
        # Creating dictionaries
        if cmd == b'CRF':
            make_dir(data[1].decode(FORMAT))
            client.send(b'ACK')
            continue
        # Our sign to stop importing files
        if cmd == b'DONE':
            break


# --------------------------
# A func that creates paths of dictionaries
def make_dir(path):
    full_path = os.path.join(ClINET_PATH, path)
    try:
        os.mkdir(full_path)
    except OSError:
        print("Creation of the directory %s failed" % path)
    else:
        print("Successfully created the directory %s " % path)


# --------------------------
# Information function about change of files location
def mov_server(data):
    set_size(data)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
    client.send(data)
    client.close()


# ---------------------------
# implement like server
# need to implement a backup from a given library
def upload_file_content(path):
    for root, dirs, files in os.walk(path, topdown=True):
        for name in files:
            full_path = os.path.join(root, name)
            delivered_path = return_path(full_path)
            upload(make_data(['UPLOAD', delivered_path]))
            print(os.path.join(root, name))
        for name in dirs:
            full_path = os.path.join(root, name)
            delivered_path = return_path(full_path)
            upload(make_data(['UPLOAD', delivered_path]))
            print(os.path.join(root, name))

    print("DONE SENDING FIRST CONNECTION")
    return


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


# -----------------------------------------
# first_connection - will connect to the server
# and send him the identifier and computer id
# return the identifier
def first_connection(computer_id):
    # check if it got user name
    if len(sys.argv) == 5:
        data = make_data(["NEW_USER", computer_id])

    # connect to the server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
    receive_flag = False
    # will send data and receive
    while True:
        if receive_flag:
            data = client.recv(SIZE)
        data_list = data.split(b"$")
        cmd = data_list[0]
        if cmd == b"NEW_USER":
            client.send(data)
            receive_flag = True
            continue
        elif cmd == b"CONNECT":
            identifier = data_list[2]
            client.send(data)
            break
        elif cmd == b"NEW_USER_ID":
            identifier = data_list[1].decode(FORMAT)
            print(identifier)
            break
    client.close()
    # return the identifier
    return identifier


# --------------------------------
# set_size compute the size of packet and send
# so the next command will not interfere
def set_size(data):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
    size_of_next_data = sys.getsizeof(data)
    client.send(make_data(['SET_SIZE', str(size_of_next_data)]))
    client.close()


# ------------------------------
# upload - will uploaded a file or if it
# is a dir it will send the  server to open
def upload(data):
    data_list = data.split(b"$")
    path_event = data_list[1].decode(FORMAT)
    path = ClINET_PATH + path_event
    if not os.path.exists(path):
        return
    print("printing from upload the path " + path)
    flag_it_dir = False
    # if its adir sed to make one
    if os.path.isdir(path):
        flag = 'CRF'
        send_data_if_dir = make_data([flag, path_event])
        flag_it_dir = True

    set_size(data)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
    if flag_it_dir:
        client.send(send_data_if_dir)
        print("Disconnected from the server from func upload with flag dir.")
        client.close()
        return

    client.send(data)
    # will read the file and set as byts
    # and send it
    time.sleep(0.2)

    file_to_send = open(path, "rb")
    data = file_to_send.read(1024)
    while data:
        print("Sending...")
        client.send(data)
        data = file_to_send.read(1024)
    file_to_send.close()
    print("Done Sending.")
    print("Disconnected from the server from fun upload.")
    client.close()
    return


# -------------------
# socket_del will send the server to delete the file

def packet_send(data):
    set_size(data)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
    client.send(data)
    print(data.decode(FORMAT))
    return


def notify_created(event):
    if not os.path.exists(event.src_path):
        return
    subs = ["xml", "goutputstream", "~", "tmp"]
    for s in subs:
        if s in event.src_path:
            return
    print(event.src_path[1:])
    full_path = event.src_path
    delivered_path = return_path(full_path)

    upload(make_data(['UPLOAD', delivered_path]))


def notify_deleted(event):
    subs = ["xml", "goutputstream", "~"]
    for s in subs:
        if s in event.src_path:
            return

    full_path = event.src_path
    delivered_path = return_path(full_path)
    packet_send(make_data(['DELETE', delivered_path]))
    # print(f"what the f**k! Someone deleted {event.src_path}!")


def notify_modified(event):
    # subs = ["xml", "goutputstream", "~"]
    # for s in subs:
    #     if s in event.src_path:
    #         return
    print(f"hey buddy, {event.src_path} has been modified")
    # full_path = event.src_path
    # delivered_path = return_path(full_path)
    # packet_send(make_data(['MODI', delivered_path]))
    # upload(make_data(['UPLOAD', delivered_path]))


def notify_moved(event):

    subs = ["xml", "~"]
    for s in subs:
        if s in event.src_path:
            return

    print(f"ok ok ok, someone moved {event.src_path} to {event.dest_path}")
    full_path_src = event.src_path
    delivered_path_src = return_path(full_path_src)
    full_path_dest = event.dest_path
    delivered_path_dest = return_path(full_path_dest)
    # check if file was edited text
    if '.goutputstream' in event.src_path or 'tmp' in event.src_path:
        packet_send(make_data(['DELETE', delivered_path_dest]))
        upload(make_data(['UPLOAD', delivered_path_dest]))
        return
    # check if the file has the same name
    file_rename = False
    if delivered_path_src.split("/")[-1] != delivered_path_dest.split("/")[-1]:
        file_rename = True

    # if true file is rename- will delete file and upload from beginning
    if file_rename:
        if os.path.isdir(event.dest_path):
            data_mov = ['RENAME_DIR', delivered_path_src, delivered_path_dest]
            packet_send(make_data(data_mov))
        else:
            packet_send(make_data(['DELETE', delivered_path_src]))
            upload(make_data(['UPLOAD', delivered_path_dest]))

    # false, so move file
    else:
        data_mov = ['MOVE', delivered_path_src, delivered_path_dest]
        mov_server(make_data(data_mov))


# ----------------------------------------
# When there is no ID, importing from server
def get_id(computer_id):
    return first_connection(make_data(["CONNECT", computer_id]))


# ----------------------------------------
# Generates id for computer
def id_generator(size=3, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def main():
    computer_id = id_generator()
    # no ID
    if len(sys.argv) == 5:
        identifier = first_connection(computer_id)
        upload_file_content(ClINET_PATH)
    # There is ID
    if len(sys.argv) == 6:
        identifier = sys.argv[5]
        make_dir(ClINET_PATH)
        second_connection(identifier, computer_id)

    patterns = ["*"]
    ignore_patterns = None
    ignore_directories = False
    case_sensitive = True
    event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)
    event_handler.on_created = notify_created
    event_handler.on_deleted = notify_deleted
    event_handler.on_modified = notify_modified
    event_handler.on_moved = notify_moved
    path = ClINET_PATH
    go_recursively = True
    my_observer = Observer()
    my_observer.schedule(event_handler, path, recursive=go_recursively)
    my_observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        my_observer.stop()
        my_observer.join()


if __name__ == "__main__":
    main()