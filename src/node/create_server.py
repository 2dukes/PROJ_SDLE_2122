import asyncio
from utils import *
from node.kademliaServer import KademliaServer
from os import getenv

def create_server(is_bootstrap_node):
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)

    port = int(getenv('BOOTSTRAP_PORT')) if is_bootstrap_node else find_free_port()
    
    kademlia_server = KademliaServer(ip=getenv('BOOTSTRAP_IP'), port=port, loop=event_loop)

    return kademlia_server