import socket
import sys
from contextlib import closing
import ntplib
import asyncio
from datetime import timezone, datetime, timedelta
import json
import ssl
from time import sleep
from colored import bg, style

def get_time_to_compare():
    return str(datetime.strptime(get_time(), '%Y-%m-%d %H:%M:%S.%f%z') - timedelta(minutes=1))

async def make_connection(host, port, msg_content):
    try:
        ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ssl_context.check_hostname = False
        ssl_context.load_verify_locations('keys/pymotw.crt')

        reader, writer = await asyncio.open_connection(
            host, port,ssl=ssl_context)

        writer.write(json.dumps(msg_content).encode())
        writer.write(b'\x00')

        data = ""
        terminate = False
        while not terminate:
            aux_data = (await reader.read(128))
            terminate = aux_data.endswith(b'\x00')
            aux_data = aux_data.rstrip(b'\x00')
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
