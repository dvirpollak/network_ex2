import os
from os import listdir
from os.path import isfile, join

#function to make a dir in the server
#args user_id = the user file
def make_dir(user_id):
    path = os.path.join(os.getcwd(), user_id)
    print(path)
    try:
        os.mkdir(path)
    except OSError:
        print("Creation of the directory %s failed" % path)
    else:
        print("Successfully created the directory %s " % path)


#clear a folder and with al contents
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


# clear_folder(os.getcwd()+"/"+"dvir"+ "/")

print(os.path.isdir(os.getcwd()+"/"+"dvir"+ "/"))
# make_dir("dvir")

#riplace a file and folders to difent dir
# os.replace(os.getcwd()+"/"+"hadar"+ "/"+"text",os.getcwd()+"/"+"dvir"+ "/"+"text")