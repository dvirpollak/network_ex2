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


def make_data(all_data):
    full_data = ""
    token = "$"
    for data in all_data:
        full_data += data + token
    return full_data


def first_connection():
    computer_id = id_generator()
    if len(sys.argv) < 6:
        data = make_data(["NEW_USER", computer_id])
        # print("I GOT ONE!")
    if len(sys.argv) > 5:
        identifier = sys.argv[5]
        data = make_data(["CONNECT", computer_id, identifier])

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
    receive_flag = False

    while True:
        if receive_flag:
            data = client.recv(SIZE).decode(FORMAT)

        data_list = data.split("$")
        cmd = data_list[0]

        if cmd == "NEW_USER":
            client.send(data.encode(FORMAT))
            receive_flag = True
            continue
        elif cmd == "CONNECT":
            identifier = data_list[2]
            client.send(data.encode(FORMAT))
            break
        elif cmd == "NEW_USER_ID":
            identifier = data_list[1]
            print(identifier)
            break

    print("Disconnected from the server.")
    client.close()
    return identifier


def receive_and_send(data):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
    receive_flag = False
    if len(data) == 0:
        receive_flag = True

    while True:
        if receive_flag:
            data = client.recv(SIZE).decode(FORMAT)
            data_list = data.split("$")
            cmd = data_list[0]
        else:
            data_list = data.split("$")
            cmd = data_list[0]

        if cmd == "LIST":
            client.send(cmd.encode(FORMAT))
        elif cmd == "DELETE":
            client.send(f"{cmd}@{data[1]}".encode(FORMAT))
        elif cmd == "UPLOAD":
            path = data_list[1].split(".")[-1]
            if os.path.isdir(path):
                flag = 'CRF'
                send_data = make_data([flag, path])
                client.send(send_data.encode(FORMAT))
                break

            # with open(f"{path}", "rb") as f:
            #     text = f.read()
            #
            # filename = path.split("/")[-1]
            # send_data = f"{cmd}@{filename}@{text}"
            # client.send(send_data.encode(FORMAT))
    print("Disconnected from the server.")
    client.close()
    return


def on_created(event):
    print(f"hey, {event.src_path} has been created!")
    subs = ["xml", "goutputstream","~"]
    for s in subs:
        if s in event.src_path:
            return
    print(event.src_path)
    receive_and_send(make_data(['UPLOAD', event.src_path]))


def on_deleted(event):
    subs = "xml"
    if subs in event.src_path:
        return
    # socket_del(event.src_path)
    print(f"what the f**k! Someone deleted {event.src_path}!")


def on_modified(event):
    subs = "xml"
    if subs in event.src_path:
        return
    receive_and_send('mod', event.src_path)
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
