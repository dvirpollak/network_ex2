# Hadar Pinto 316460146
# Dvir Pollak 318528627
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
# GLOBALS
TOKEN_IN_BYTES = b'$'
UPDATE = 'Waiting for command'
REC_ACK = sys.getsizeof(b"ACK")
identifier = ''
computer_id = ''


# function to create a folder with a given path
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


# This function will run and will check if there are any updates from the server
def client_is_listening():
    global UPDATE
    size = 1024
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
    client.send(make_data(['CHECK_FOR_UPDATE', computer_id, identifier]))
    while True:
        UPDATE = 'Waiting for update'
        data = client.recv(size)
        data = data.split(TOKEN_IN_BYTES)
        cmd = data[0]
        # for preparation, to know the size of the command we'll get
        if cmd == b"SET_SIZE":
            size = int(data[1].decode(FORMAT))
            continue
        # creates file
        elif cmd == b'CRF':
            UPDATE = data[1].decode(FORMAT)
            make_dir(data[1].decode(FORMAT)[1:])
            client.send(REC_ACK)
            continue

        # upload file
        elif cmd == b"UPLOAD":
            UPDATE = data[1].decode(FORMAT)[1:]
            path_to_put = data[1].decode(FORMAT)[1:]
            filepath = os.path.join(ClINET_PATH, path_to_put)  # we need to check after change
            client.send(REC_ACK)

            # write bytes into downloaded file
            file_to_down = open(filepath, "wb")
            len_of_data_rec = client.recv(1024)
            while len_of_data_rec:
                file_to_down.write(len_of_data_rec)
                len_of_data_rec = client.recv(1024)
            file_to_down.close()

            file_to_down.close()
            client.send(REC_ACK)
            continue
        # delete the file
        elif cmd == b"DELETE":
            UPDATE = data[1].decode(FORMAT)[1:]
            event_path_del = data[1].decode(FORMAT)[1:]
            path_del = os.path.join(ClINET_PATH, event_path_del)  # check after change
            try:
                if os.path.isfile(path_del):
                    os.unlink(path_del)
                else:  # if it's a directory it will delete it
                    clear_folder(path_del)

            except OSError:
                pass
            client.send(REC_ACK)
            continue
        # move file from source_path to destination_path
        elif cmd == b"MOVE":
            UPDATE = data[1].decode(FORMAT)[1:]
            source_path = os.path.join(ClINET_PATH, data[1].decode(FORMAT)[1:])
            destination_path = os.path.join(ClINET_PATH, data[2].decode(FORMAT)[1:])
            if not os.path.exists(source_path):
                client.send(REC_ACK)
                continue
            os.replace(source_path, destination_path)
            client.send(REC_ACK)
            continue
        # Renaming file or directory
        elif cmd == b"RENAME_DIR":
            UPDATE = data[1].decode(FORMAT)[1:]
            source_path = os.path.join(ClINET_PATH, data[1].decode(FORMAT)[1:])
            destination_path = os.path.join(ClINET_PATH, data[2].decode(FORMAT)[1:])
            try:
                os.rename(source_path, destination_path)
            except OSError:
                pass
            client.send(REC_ACK)
            continue
        elif cmd == b'NO_UPDATES':
            client.send(b'SYN')
            break
    client.close()


# This func will return boolean, if the file exist or not
def is_file_in_dict(event, path):
    file_list = []

    for root, dirs, files in os.walk(path):
        for file in files:
            file_list.append(os.path.join(root, file))

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
        data = data.split(TOKEN_IN_BYTES)
        cmd = data[0]
        # adjusting size
        if cmd == b'SET_SIZE':
            size = int(data[1].decode(FORMAT))
            client.send(REC_ACK)
            continue
        # Receiving files from server
        if cmd == b'UPLOAD_FILE':
            file_to_down = open(os.path.join(ClINET_PATH, data[1].decode(FORMAT)), "wb")
            size_file = int(data[2].decode(FORMAT))
            client.send(REC_ACK)
            file_receive = client.recv(size_file)
            counter_bytes = 0
            while file_receive:
                file_to_down.write(file_receive)
                counter_bytes += len(file_receive)
                if counter_bytes == size_file:
                    break
                file_receive = client.recv(1024)
            file_to_down.close()
            client.send(REC_ACK)
            continue
        # Creating dictionaries
        if cmd == b'CRF':
            make_dir(data[1].decode(FORMAT))
            client.send(REC_ACK)
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
        pass
    else:
        pass


# ---------------------------
# This function will take all file, store them in a list with the commands
def upload_file_content(path):
    data_list = []
    for root, dirs, files in os.walk(path, topdown=True):
        for name in files:
            full_path = os.path.join(root, name)
            delivered_path = return_path(full_path)
            data_list.append(make_data(['UPLOAD', delivered_path, str(os.path.getsize(full_path))]))
            print(os.path.join(root, name))
        for name in dirs:
            full_path = os.path.join(root, name)
            delivered_path = return_path(full_path)
            data_list.append(make_data(['CRF', delivered_path]))
            print(os.path.join(root, name))

    return data_list


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
    data_list = upload_file_content(ClINET_PATH)
    data_list.insert(0, make_data(["NEW_USER", computer_id]))
    send_server(data_list)


# --------------------------------
# set_size compute the size of packet and send
# so the next command will not interfere
def set_size(data):
    size_of_next_data = sys.getsizeof(data) + sys.getsizeof(identifier) + sys.getsizeof(computer_id)
    return make_data(['SET_SIZE', str(size_of_next_data), identifier, computer_id])


# main function to send commands to server
def send_server(list_of_updates):
    global identifier
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)

    while list_of_updates:

        full_data = list_of_updates.pop(0)
        client.send(set_size(full_data))
        client.recv(REC_ACK)
        data = full_data.split(TOKEN_IN_BYTES)
        cmd = data[0]

        if cmd == b"NEW_USER":
            client.send(full_data)
            identifier = client.recv(128).decode(FORMAT)  # for ID
            continue
        if cmd == b"DELETE":
            client.send(full_data)
            client.recv(REC_ACK)
            continue
        # Receiving files from server
        if cmd == b'UPLOAD':
            client.send(full_data)
            file_to_send = open(os.path.join(ClINET_PATH, data[1].decode(FORMAT)[1:]), "rb")
            client.recv(REC_ACK)
            data = file_to_send.read()
            client.send(data)
            file_to_send.close()
            client.recv(REC_ACK)
            continue
        # Creating dictionaries
        if cmd == b'CRF':
            client.send(full_data)
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

    client.send(b'SYN')
    client.close()
    return


# When the watch dog says a file has created, this function will send the file
def notify_created(event):
    if not os.path.exists(event.src_path):
        return
    # temporary files or irrelevant commands
    subs = ["xml", "goutputstream", "~", "tmp", UPDATE]
    for s in subs:
        if s in event.src_path:
            return
    full_path = event.src_path
    delivered_path = return_path(full_path)
    temp_file_size = os.path.getsize(full_path)
    # for large files
    while temp_file_size != os.path.getsize(full_path):
        temp_file_size = os.path.getsize(full_path)
        time.sleep(0.2)
    if os.path.isfile(event.src_path):
        send_server([make_data(['UPLOAD', delivered_path, str(os.path.getsize(full_path))])])

    else:  # if it a dir it will delete the dir
        send_server([make_data(['CRF', delivered_path])])


# watch says file has been deleted
def notify_deleted(event):
    subs = ["xml", "goutputstream", "~", UPDATE]
    for s in subs:
        if s in event.src_path:
            return
    full_path = event.src_path
    delivered_path = return_path(full_path)
    send_server([make_data(['DELETE', delivered_path])])


# irrelevant
def notify_modified(event):
    pass


# for moving file, renaming
def notify_moved(event):

    subs = ["xml", "~", UPDATE]
    for s in subs:
        if s in event.src_path:
            return
    full_path_src = event.src_path
    delivered_path_src = return_path(full_path_src)
    full_path_dest = event.dest_path
    delivered_path_dest = return_path(full_path_dest)
    # check if file was edited text
    if '.goutputstream' in event.src_path or 'tmp' in event.src_path:
        send_server([make_data(['DELETE', delivered_path_dest]), make_data(['UPLOAD',
                    delivered_path_dest, str(os.path.getsize(full_path_dest))])])
        return
    # check if the file has the same name
    file_rename = False
    if delivered_path_src.split("/")[-1] != delivered_path_dest.split("/")[-1]:
        file_rename = True

    # if true file is rename- will delete file and upload from beginning
    if file_rename:
        if os.path.isdir(event.dest_path):
            data_mov = ['RENAME_DIR', delivered_path_src, delivered_path_dest]
            send_server([make_data(data_mov)])
        else:

            send_server([make_data(['UPLOAD', delivered_path_dest,str(os.path.getsize(full_path_dest))]),
                         make_data(['DELETE', delivered_path_src])])

    # false, so move file
    else:
        data_mov = ['MOVE', delivered_path_src, delivered_path_dest, identifier, computer_id]
        send_server([make_data(data_mov)])


# ----------------------------------------
# When there is no ID, importing from server
def get_id():
    return first_connection(make_data(["CONNECT", computer_id]))


# ----------------------------------------
# Generates id for computer
def id_generator(size=3, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def main():
    global computer_id, identifier
    computer_id = id_generator()
    # no ID
    if len(sys.argv) == 5:
        first_connection()

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
            # time to update sever
            time.sleep(time_connect)
            client_is_listening()
    except KeyboardInterrupt:
        my_observer.stop()
        my_observer.join()


if __name__ == "__main__":
    main()