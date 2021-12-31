import socket
import sys
from contextlib import closing

def print_log(msg):
    with open("logfile.log", "a+") as file:
        file.write(str(msg) + "\n")

def read_port():
    with open("ports.txt", "r") as file:
        port = file.read()
    return int(port)

def is_port_in_use(port):
    # import socket
    # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    #     return s.connect_ex(('localhost', port)) == 0

    a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    location = ("localhost", port)
    result_of_check = a_socket.connect_ex(location)

    a_socket.close()

    return result_of_check

def find_free_port():
    if (not is_port_in_use(6000)):
        return 6000
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

def signal_handler(sig, frame):
    print('Exiting node...')
    sys.exit(1)
