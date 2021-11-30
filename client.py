import socket
import sys
import os
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from watchdog.events import LoggingEventHandler
import random
import string


def id_generator(size=3, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def get_id(computer_id):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip_address, server_port))
    token = '$'
    message = 'Hi' + token + computer_id
    s.send(bytes(message, 'utf-8'))
    data = s.recv(1024)
    s.shutdown(2)
    s.close()
    return str(data, 'utf-8')


def socket_del(event_path):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip_address, server_port))
    token = '$'
    flag = 'del'
    message = identifier + token + flag + token + event_path
    message_in_bytes = bytes(str(message), 'utf-8')
    s.send(message_in_bytes)
    # maybe check if he got the message properly
    s.shutdown(2)
    s.close()


def socket_mov(source_path, dst_path):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip_address, server_port))
    token = '$'
    flag = 'mov'
    message = identifier + token + flag + token + source_path + token + dst_path
    message_in_bytes = bytes(str(message), 'utf-8')
    s.send(message_in_bytes)
    # maybe check if he got the message properly
    s.shutdown(2)
    s.close()


def socket_send(flag, event_path):
    boolean = os.path.isdir(event_path)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip_address, server_port))
    token = '$'
    if boolean:
        flag = 'crf'
        message = flag + token + identifier + token + event_path
        message_in_bytes = bytes(str(message), 'utf-8')
        s.send(message_in_bytes)
        s.close()
        return
    message = flag + token + identifier + token + event_path
    message_in_bytes = bytes(str(message), 'utf-8')
    s.send(message_in_bytes)
    file_name = event_path.split('.')
    #print(file_name + "here")
    file_to_send = open(os.getcwd()+file_name[1], "rb")
    data = file_to_send.read(1024)
    while data:
        print("Sending...")
        s.send(data)
        data = file_to_send.read(1024)
    file_to_send.close()
    s.send(b"DONE")
    print("Done Sending.")
    print(s.recv(1024))
    s.shutdown(2)
    s.close()
    return

    # while True:
    #    data = s.recv(1000)
    #    s.send(bytes('FIN', 'utf-8'))
    #    print("Server sent: ", str(data, 'utf-8'))
    #    if str(data, 'utf-8') == 'FIN':
    #        s.close()
    #        break


def on_created(event):
    print(f"hey, {event.src_path} has been created!")
    subs = "xml"
    if subs in event.src_path:
        return
    socket_send('cr', event.src_path)


def on_deleted(event):
    socket_del(event.src_path)
    print(f"what the f**k! Someone deleted {event.src_path}!")


def on_modified(event):
    subs = "xml"
    if subs in event.src_path:
        return
    socket_send('mod', event.src_path)
    print(f"hey buddy, {event.src_path} has been modified")


def on_moved(event):
    socket_mov(event.src_path, event.dest_path)
    print(f"ok ok ok, someone moved {event.src_path} to {event.dest_path}")


if __name__ == "__main__":
    comp_id = id_generator()
    ip_address = sys.argv[1]
    server_port = int(sys.argv[2])
    path_file = sys.argv[3]
    time_connect = int(sys.argv[4])
    identifier = "ABCD"
    if len(sys.argv) < 6:
        identifier = get_id(comp_id)
        print("I GOT ONE!")
    if len(sys.argv) > 5:
        identifier = sys.argv[5]
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
