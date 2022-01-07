import socket
import sys
from contextlib import closing
import ntplib
import asyncio
from datetime import timezone, datetime, timedelta
import json
from time import sleep

def get_time_to_compare():
    return str(datetime.strptime(get_time(), '%Y-%m-%d %H:%M:%S.%f%z') - timedelta(minutes=1))


async def make_connection(host, port, msg_content):
    try:
        reader, writer = await asyncio.open_connection(
            host, port)

        print_log(msg_content)
        writer.write(json.dumps(msg_content).encode())
        writer.write_eof()

        data = await reader.read()
        response = json.loads(data.decode())

        writer.close()
        return response

    except Exception as err:
        print_log(err)
        return None

def get_time():
    while True:
        try:
            c = ntplib.NTPClient()
            response = c.request('pool.ntp.org', version=3)
            return str(datetime.fromtimestamp(response.tx_time + response.delay / 2, timezone.utc))
        except Exception as err:
            print_log(err)
            sleep(1)

def print_log(msg):
    with open("logfile.log", "a+") as file:
        file.write(str(msg) + "\n")


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def signal_handler(sig, frame):
    print('Exiting node...')
    sys.exit(1)
