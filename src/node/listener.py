import asyncio
from asyncio.events import new_event_loop
from threading import Thread
import json
import time

from utils import print_log, make_connection


async def wait_for_msgs(reader, writer, kademlia_server):
    print_log("Entered wait_for_msgs!")
    server = kademlia_server.server

    while True:
        try:
            print_log("66666666")
            msg = json.loads((await reader.read()).decode())
            print_log("777777777")
            msg_type = msg["msg_type"]
            print_log("Listener: " + str(msg_type))
            my_data = kademlia_server.get_info()
            print_log("888888888")

            if msg_type == "FOLLOW":
                print_log("999999999")
                my_data["followers"].append(msg["following"])
                server.set(kademlia_server.username, my_data)

                print_log("AAAAAAA")

                response = {"msg_type": "ACK_FOLLOW"}

            elif msg_type == "GET":
                timestamp = msg["timestamp"]

                my_messages = my_data["messages"]

                response = list(
                    filter(lambda x: x[1] > timestamp, my_messages))
            else:
                print_log("Invalid message type received!")

            print_log("BBBBBBBBBBB")
            writer.write(response)
            print_log("CCCCCCCC")
            await writer.drain()
            print_log("DDDDDDDDDD")
        except Exception as err:
            print_log("Listener Error: " + str(err))


def test(r, w):
    while True:
        time.sleep(5)
        print_log('ENTERED TEST')


class Listener(Thread):
    def __init__(self, ip, port, kademlia_server):
        super(Listener, self).__init__()
        self.ip = ip
        self.port = port
        self.kademlia_server = kademlia_server

    def run(self):
        print_log("IM HERE2.1")
        self.loop = asyncio.new_event_loop()
        print_log("IM HERE2.2")
        self.loop.run_until_complete(self.setup_server())
        print_log("IM HERE2.25")

    async def setup_server(self):
        try:
            print_log("IM HERE2.3")
            self.server = await asyncio.start_server(test, self.ip, self.port)
            # self.server = await asyncio.start_server(lambda r, w: wait_for_msgs(r, w, self.kademlia_server), self.ip, self.port)
            print_log("IM HERE2.4")
            await self.server.serve_forever()
            print_log("IM HERE2.5")
        except Exception as err:
            print_log(str(err))
