import socket
import sys
import os
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from watchdog.events import LoggingEventHandler
import random
import string

ADDR = (sys.argv[1], int(sys.argv[2]))
FORMAT = "utf-8"
SIZE = 1024
ClINET_PATH = sys.argv[3]
time_connect = int(sys.argv[4])


# ---------------------------
# need to implement a backup from a given library
def upload_file_content(path):
    for root, dirs, files in os.walk(".", topdown=True):
        for name in files:
            upload(make_data(['UPLOAD', os.path.join(root, name)[1:]]))
            print(os.path.join(root, name))
        for name in dirs:
            upload(make_data(['UPLOAD', os.path.join(root, name)[1:]]))
            print(os.path.join(root, name))

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
# first_connection - will connect to the sever
# and send him the identifier and computer id
# return the identifier
def first_connection():
    computer_id = id_generator()
    # check if it got user name
    if len(sys.argv) < 6:
        data = make_data(["NEW_USER", computer_id])
    if len(sys.argv) > 5:
        identifier = sys.argv[5]
        data = make_data(["CONNECT", computer_id, identifier])

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

    print("Disconnected from the server.")
    client.close()
    # return the identifier
    return identifier


# --------------------------------
# set_size compute the size of message and send
# so the next commend will not interfere
def set_size(data):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
    size_of_next_data = sys.getsizeof(data)
    client.send(make_data(['SET_SIZE', str(size_of_next_data)]))
    client.close()


# ------------------------------
# upload - will uploaded a file or if it
# is a dir it will send the the server to opne
def upload(data):
    data_list = data.split(b"$")
    path_event = data_list[1].decode(FORMAT)
    path = ClINET_PATH + path_event
    print(path)
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
        print("Disconnected from the server.")
        client.close()
        return

    client.send(data)
    # will read the file and set as byts
    # and send it
    filetosend = open(path, "rb")
    data = filetosend.read(1024)
    while data:
        print("Sending...")
        client.send(data)
        data = filetosend.read(1024)
    filetosend.close()
    print("Done Sending.")

    print("Disconnected from the server.")
    client.close()
    return


# -------------------
# socket_del will send the server to delete the file

def socket_del(data):
    set_size(data)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
    client.send(data)
    print(data.decode(FORMAT))
    return


def on_created(event):
    print(f"hey, {event.src_path} has been created!")
    subs = ["xml", "goutputstream", "~"]
    for s in subs:
        if s in event.src_path:
            return
    print(event.src_path[1:])
    upload(make_data(['UPLOAD', event.src_path[1:]]))


def on_deleted(event):
    subs = ["xml", "goutputstream", "~"]
    for s in subs:
        if s in event.src_path:
            return
    socket_del(make_data(['DELETE', event.src_path[1:]]))
    print(f"what the f**k! Someone deleted {event.src_path}!")


def on_modified(event):
    subs = ["xml", "goutputstream", "~"]
    for s in subs:
        if s in event.src_path:
            return
    print(f"hey buddy, {event.src_path} has been modified")


def on_moved(event):
    # socket_mov(event.src_path, event.dest_path)
    print(f"ok ok ok, someone moved {event.src_path} to {event.dest_path}")


def get_id(computer_id):
    return first_connection(make_data(["CONNECT", computer_id]))


def id_generator(size=3, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def main():
    identifier = first_connection()
    print(identifier)
    if len(sys.argv) < 6:
        upload_file_content(ClINET_PATH)
    patterns = ["*"]
    ignore_patterns = None
    ignore_directories = False
    case_sensitive = True
    my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)
    my_event_handler.on_created = on_created
    my_event_handler.on_deleted = on_deleted
    my_event_handler.on_modified = on_modified
    my_event_handler.on_moved = on_moved
    path = "."
    go_recursively = True
    my_observer = Observer()
    my_observer.schedule(my_event_handler, path, recursive=go_recursively)
    my_observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        my_observer.stop()
        my_observer.join()


if __name__ == "__main__":
    main()