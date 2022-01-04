import socket
import sys
from contextlib import closing
import ntplib
import asyncio
from datetime import timezone, datetime
import json
import time


async def make_connection(host, port, msg_content):
    try:
        time.sleep(5)
        print_log("11111111")
        (reader, writer) = await asyncio.open_connection(host, port)
        print_log("22222222")
        writer.write(json.dumps(msg_content).encode())
        print_log("33333333")
        await writer.drain()
        print_log("44444444")
        response = await reader.read()
        print_log("55555555")
        return json.loads(response.decode())
    except Exception as err:
        print_log(err)
        return None


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


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def signal_handler(sig, frame):
    print('Exiting node...')
    sys.exit(1)
