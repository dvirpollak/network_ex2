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
def second_connection(identifier):
    computer_id = id_generator()
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
def first_connection():
    computer_id = id_generator()
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

def file_deletion(data):
    set_size(data)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
    client.send(data)
    print(data.decode(FORMAT))
    return


def notify_created(event):
    subs = ["xml", "goutputstream", "~"]
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
    file_deletion(make_data(['DELETE', delivered_path]))
    # print(f"what the f**k! Someone deleted {event.src_path}!")


def notify_modified(event):
    subs = ["xml", "goutputstream", "~"]
    for s in subs:
        if s in event.src_path:
            return
    # print(f"hey buddy, {event.src_path} has been modified")


def notify_moved(event):
    subs = ["xml", "goutputstream", "~"]
    for s in subs:
        if s in event.src_path:
            return

    full_path_src = event.src_path
    delivered_path_src = return_path(full_path_src)
    full_path_dst = event.dst_path
    delivered_path_dst = return_path(full_path_dst)
    data_mov = ['MOVE', delivered_path_src, delivered_path_dst]
    mov_server(make_data(data_mov))
    # print(f"ok ok ok, someone moved {event.src_path} to {event.dest_path}")


# ----------------------------------------
# When there is no ID, importing from server
def get_id(computer_id):
    return first_connection(make_data(["CONNECT", computer_id]))


# ----------------------------------------
# Generates id for computer
def id_generator(size=3, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def main():
    # no ID
    if len(sys.argv) == 5:
        identifier = first_connection()
        upload_file_content(ClINET_PATH)
    # There is ID
    if len(sys.argv) == 6:
        identifier = sys.argv[5]
        make_dir(ClINET_PATH)
        second_connection(identifier)
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