import logging
import asyncio
import json

from kademlia.network import Server
from threading import *
from utils import print_log
from hashlib import sha256

class KademliaServer:
    def __init__(self, port, loop):
        self.port = port
        self.loop = loop

        self.server = Server()
        self.loopThread = Thread(target=self.start_server)
        self.loopThread.start()
        
    def start_server(self):
        handler = logging.FileHandler('log_kademlia.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        log = logging.getLogger('kademlia')
        log.addHandler(handler)
        log.setLevel(logging.DEBUG)

        self.loop.set_debug(True)
        # self.loop = asyncio.get_event_loop()
        
        self.loop.run_until_complete(self.server.listen(self.port))
        
        # Testing purposes (hard-coded)
        bootstrap_node = [("localhost", 6000)]
        self.loop.run_until_complete(self.server.bootstrap(bootstrap_node))
        
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.server.stop()
            self.loop.close()

    def close_server(self):
        # Closes the loop after the current iteration
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.server.close()

    async def network_login(self, username, plain_password):
        response = await self.server.get(username)

        if response is not None:
            user_state = json.loads(response)
            hashed_password = sha256(plain_password.encode('utf-8')).hexdigest()

            if user_state['password'] != hashed_password:
                print_log(f"Incorrect password for user {username}.")
                return False
        
            return True
        else:
            print_log(f"Username {username} doesn\'t exist.")
            return False
        
    async def network_register(self, username, plain_password):
        response = await self.server.get(username)

        if response is None:
            hashed_password = sha256(plain_password.encode('utf-8')).hexdigest()
            
            user_state = {}
            user_state['password'] = hashed_password
            user_state['followers'] = []
            user_state['following'] = []
            user_state['messages'] = []
            
            await self.server.set(username, json.dumps(user_state))
            return True
        else:
            print_log(f"Username {username} already exists.")    
            return False
        