import socket
import sys
from contextlib import closing
import ntplib
from datetime import timezone, datetime

def get_time():
    try:
        c = ntplib.NTPClient()
        response = c.request('pool.ntp.org', version=3)
        return datetime.fromtimestamp(response.tx_time + response.delay / 2, timezone.utc)
    except Exception:
        return "Couldn't get time!"

def print_log(msg):
    with open("logfile.log", "a+") as file:
        file.write(str(msg) + "\n")

def is_port_in_use(port):
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
