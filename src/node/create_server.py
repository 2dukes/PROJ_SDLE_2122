import asyncio
from utils import *
from node.kademliaServer import KademliaServer

def create_server(is_bootstrap_node):
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)

    port = 6000 if is_bootstrap_node else find_free_port()

    kademlia_server = KademliaServer(port=port, loop=event_loop)

    return {
        "server": kademlia_server.server,
        "loop": event_loop,
        "port": port,
    }