import asyncio
from asyncio.events import new_event_loop
from threading import Thread
import json
import time

from utils import print_log, make_connection

async def wait_for_msgs(reader, writer, kademlia_server):
    print_log("Entered wait_for_msgs!")
    server = kademlia_server.server
    
    data = await reader.read()

    msg = json.loads(data.decode())
    msg_type = msg['msg_type']
    my_data = await kademlia_server.get_info()

    if msg_type == "FOLLOW":
        my_data["followers"].append(msg["following"])
        await server.set(kademlia_server.username, json.dumps(my_data))

        response = {"msg_type": "ACK_FOLLOW"}
    elif msg_type == "UNFOLLOW":
        my_data["followers"].remove(msg["unfollowing"])
        await server.set(kademlia_server.username, json.dumps(my_data))

        response = {"msg_type": "ACK_UNFOLLOW"}
    elif msg_type == "ACK_UNFOLLOW":
        username_to_unfollow = msg["username"]
        for unfollower in my_data["pending_unfollow"]:
            if username_to_unfollow == unfollower:
                my_data["pending_unfollow"].remove(unfollower)
                break

        await server.set(kademlia_server.username, json.dumps(my_data)) 
        response = {"msg_type": "ACK_UNFOLLOW_OK"}
    # elif msg_type == "ACK_FOLLOW":
        # username_to_follow = msg["username"]
        # my_data["pending_followers"].remove(username_to_follow)
        # await server.set(kademlia_server.username, json.dumps(my_data))
        # response = {"msg_type": "ACK_FOLLOW_OK"}
    else:
        print_log("Invalid message type received!")

    writer.write(json.dumps(response).encode())
    writer.write_eof()
    await writer.drain()
    writer.close()

class Listener(Thread):
    def __init__(self, ip, port, kademlia_server):
        super(Listener, self).__init__()
        self.ip = ip
        self.port = port
        self.kademlia_server = kademlia_server

    def run(self):
        self.loop = asyncio.new_event_loop()
        self.loop.run_until_complete(self.setup_server())

    async def setup_server(self):
        try:
            self.server = await asyncio.start_server(lambda r, w: wait_for_msgs(r, w, self.kademlia_server), self.ip, self.port)
            await self.server.serve_forever()
        except Exception as err:
            print_log(err)
