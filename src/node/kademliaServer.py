import logging
import asyncio
import json
import datetime
from consolemenu import console_menu
from consolemenu import Screen

from kademlia.network import Server
from threading import *
from utils import print_log
from hashlib import sha256
import random

QUEUE_LIMIT = 100

class KademliaServer:
    def __init__(self, port, loop):
        self.port = port
        self.loop = loop

        self.server = Server()
        self.loopThread = Thread(target=self.start_server, daemon=True)
        self.loopThread.start()
        
    def start_server(self):
        handler = logging.FileHandler('log_kademlia.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        log = logging.getLogger('kademlia')
        log.addHandler(handler)
        log.setLevel(logging.DEBUG)

        self.loop.set_debug(True)                
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

    def close_server(self):
        self.loop.call_soon_threadsafe(self.loop.stop)

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

    async def publish(self, message, username):
        response = await self.server.get(username)
        if response is None:
            print_log(f"Username {username} does not exist.")
        else:
            data = json.loads(response)
            if len(data["messages"]) >= QUEUE_LIMIT:
                del data["messages"][0]
            data["messages"].append([message, str(datetime.datetime.now())])
            Screen.println("\n\nWriting to the network...")
            await self.server.set(username, json.dumps(data))


    async def add_following(self, my_username, username_to_follow):
        if my_username == username_to_follow:
            Screen.println("You cannot follow yourself")
            return False
        
        response = await self.server.get(my_username)
        
        if response is None:
            print_log(f"Username {my_username} does not exist.")
        else:
            Screen.println(f"\n\nFollowing {username_to_follow}...\n")
            
            data = json.loads(response)

            if not username_to_follow in data["following"]:
                data["following"].append(username_to_follow)
                await self.server.set(my_username, json.dumps(data))
                await self.add_follower(my_username, username_to_follow)                    
            else:
                print_log(f"You already follow {username_to_follow}")           
                    
    async def add_follower(self, my_username, followed_username):
        response = await self.server.get(followed_username)
        data = json.loads(response)

        if not my_username in data["followers"]:
            data["followers"].append(my_username)
            successful_follow = False
            while not successful_follow:
                await self.server.set(followed_username, json.dumps(data))

                follower_response = await self.server.get(followed_username)
                data = json.loads(follower_response)
                successful_follow = my_username in data["followers"]
                if not my_username in data["followers"]:
                    data["followers"].append(my_username)

                # CSMA/CD
                await asyncio.sleep(random.uniform(0, 5))

        else:
            print_log(f"The user {followed_username} already follows you.")                
    
    async def remove_follower(self, my_username, username_to_unfollow):
        pass

    async def remove_following(self, my_username, username_who_unfollow):
        pass


    async def get_info(self, username):
        response = await self.server.get(username)

        if response is None:
            print_log(f"Username {username} does not exist.")
        else:            
            return json.loads(response)