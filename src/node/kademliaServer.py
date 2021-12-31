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
        response = await self.server.get(f"{username}-password")

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
            
            user_password = {"password": hashed_password}
            user_followers = {"followers": []}
            user_following = {"following": []}
            user_messages = {"messages": []}
            
            await asyncio.gather(
                self.server.set(f"{username}-password", json.dumps(user_password)),
                self.server.set(f"{username}-followers", json.dumps(user_followers)),
                self.server.set(f"{username}-following", json.dumps(user_following)),
                self.server.set(f"{username}-messages", json.dumps(user_messages))
            )
    
            return True
        else:
            print_log(f"Username {username} already exists.")    
            return False

    async def publish(self, message, username):
        response = await self.server.get(f"{username}-messages")
        
        if response is None:
            print_log(f"Username {username} does not exist.")
        else:
            data = json.loads(response)
            if len(data["messages"]) >= QUEUE_LIMIT:
                del data["messages"][0]
            data["messages"].append([message, str(datetime.datetime.now())])
            Screen.println("\nWriting to the network...")
            await self.server.set(f"{username}-messages", json.dumps(data))


    async def add_following(self, my_username, username_to_follow):
        if my_username == username_to_follow:
            Screen.println("You cannot follow yourself!")
            return False
        
        username_to_follow_response = await self.server.get(f"{username_to_follow}-following")
        if username_to_follow_response is None:    
            Screen.println(f"Username {username_to_follow} does not exist.")
            return False
        
        response = await self.server.get(f"{my_username}-following")

        if response is None:
            Screen.println(f"Username {my_username} does not exist.")
        else:
            Screen.println(f"\nFollowing {username_to_follow}...")
            
            data = json.loads(response)

            if not username_to_follow in data["following"]:
                data["following"].append(username_to_follow)
                await self.server.set(f"{my_username}-following", json.dumps(data))
                await self.add_follower(my_username, username_to_follow)                    
            else:
                print_log(f"You already follow {username_to_follow}")           
                    
    async def add_follower(self, my_username, followed_username):
        response = await self.server.get(f"{followed_username}-followers")
        data = json.loads(response)

        if not my_username in data["followers"]:
            data["followers"].append(my_username)
            successful_follow = False
            while not successful_follow:
                await self.server.set(f"{followed_username}-followers", json.dumps(data))
                
                # CSMA/CD
                await asyncio.sleep(random.uniform(5, 10)) # Wait a sufficient amount of time to avoid collisions. 

                follower_response = await self.server.get(f"{followed_username}-followers")
                data = json.loads(follower_response)
                successful_follow = my_username in data["followers"]
                if not my_username in data["followers"]:
                    data["followers"].append(my_username)


        else:
            print_log(f"The user {followed_username} already follows you.")                
    
    async def remove_follower(self, my_username, username_to_unfollow):
        pass

    async def remove_following(self, my_username, username_who_unfollow):
        pass


    async def get_info(self, username):
        response = await asyncio.gather(
            self.server.get(f"{username}-password"),
            self.server.get(f"{username}-followers"),
            self.server.get(f"{username}-following"),
            self.server.get(f"{username}-messages")
        )            

        print_log(response)
        
        if response is []:
            print_log(f"Username {username} does not exist.")
        else:         
            return {
                "followers": json.loads(response[1])["followers"],
                "following": json.loads(response[2])["following"],
                "messages": json.loads(response[3])["messages"]
            }   