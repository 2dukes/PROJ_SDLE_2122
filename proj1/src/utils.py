<<<<<<< HEAD
import socket
import sys
from contextlib import closing
import ntplib
import asyncio
from datetime import timezone, datetime, timedelta
import json
import ssl
from time import sleep
from os import getenv
from colored import bg, style
from consolemenu import Screen

READ_BYTES = 128
EOF_BYTE = b'\x00'

def get_valid_password(prompt_message="Password: "):
    password = input(prompt_message)

    invalid_passwords = ["menu", ""]

    while password in invalid_passwords:
        Screen.println("\"menu\" and \"\" are not valid passwords! Please choose a different one.")
        password = input("Password: ")

    return password

def get_time_to_compare():
    return str(datetime.strptime(get_time(), '%Y-%m-%d %H:%M:%S.%f%z') - timedelta(minutes=1))

async def make_connection(host, port, msg_content):
    try:
        ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ssl_context.check_hostname = False
        ssl_context.load_verify_locations(getenv('CERT_PATH'))

        reader, writer = await asyncio.open_connection(
            host, port,ssl=ssl_context)

        writer.write(json.dumps(msg_content).encode())
        writer.write(EOF_BYTE)

        data = ""
        terminate = False
        while not terminate:
            aux_data = (await reader.read(READ_BYTES))
            terminate = aux_data.endswith(EOF_BYTE)
            aux_data = aux_data.rstrip(EOF_BYTE)
            data += aux_data.decode()

        response = json.loads(data)

        writer.close()
        return response

    except Exception as err:
        return None


def get_time():
    while True:
        try:
            c = ntplib.NTPClient()
            response = c.request('pool.ntp.org', version=3)
            return str(datetime.fromtimestamp(response.tx_time + response.delay / 2, timezone.utc))
        except Exception as err:
            sleep(1)

def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def signal_handler(sig, frame):
    print('Exiting node...')
    sys.exit(1)


def print_with_highlighted_color(to_change, content):
    divided_text = content.split(to_change)
    number_of_mentions = content.count(to_change)

    for text in divided_text:
        print(text, end="")
        if number_of_mentions > 0:
            print(bg('red') + style.BOLD +
                    to_change + style.RESET, end="")
            number_of_mentions -= 1

    print()
=======
from genericpath import exists
import re
import argparse
from os.path import exists
from os import rename, fsync
import pickle
import sys

def parseIDs(arg_value, pattern=re.compile(r"^.*_.*$")):
    if pattern.match(arg_value):
        raise argparse.ArgumentTypeError("Provided ID can't have an \"_\".")
    return arg_value

def atomic_write(file_path, data):
    tmp_file = f"{file_path}_tmp"  
    with open(tmp_file, "wb") as file:
        pickle.dump(data, file)
        file.flush()
        fsync(file.fileno())
      
    rename(tmp_file, file_path) # Atomic instruction

def read_sequence_num_pub(file_path):
    seq_num = 0
    if exists(file_path):
        seq_num = pickle.load(open(file_path, "rb"))
    return seq_num

def read_sequence_num_sub(file_path):
    seq_num = 0
    last_get_id = {}
    if exists(file_path):
        [seq_num, last_get_id] = pickle.load(open(file_path, "rb"))
    return [seq_num, last_get_id]


def signal_handler(sig, frame):
    print('Pressing CTRL+C again may allow you to quit the program')
    sys.exit(1)
>>>>>>> 4026870a1def1c454b26f458b401911efedfa4cd
