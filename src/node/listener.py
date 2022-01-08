import asyncio
from threading import Thread
import json

async def wait_for_msgs(reader, writer, kademlia_server):
    server = kademlia_server.server
    
    data = await reader.read()

    msg = json.loads(data.decode())
    msg_type = msg['msg_type']
    my_data = await kademlia_server.get_info(kademlia_server.username)

    kademlia_server.log_info(f"Listener - Received {str(msg)}")

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
    else:
        kademlia_server.log_info("Listener - Invalid message type received!", level="ERROR")

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
        self.server = await asyncio.start_server(lambda r, w: wait_for_msgs(r, w, self.kademlia_server), self.ip, self.port)
        await self.server.serve_forever()
