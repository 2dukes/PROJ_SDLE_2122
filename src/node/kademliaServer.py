import logging
import asyncio
import json
import datetime
import copy

from consolemenu import console_menu
from consolemenu import Screen
from utils import get_time

from kademlia.network import Server
from threading import *
from utils import print_log, make_connection
from hashlib import sha256
import random

from node.listener import Listener

QUEUE_LIMIT = 100
class KademliaServer:
    def __init__(self, ip, port, loop):
        self.ip = ip
        self.port = port
        self.loop = loop
        
        print_log(self.ip)
        print_log(self.port)
        self.listener = Listener(ip=self.ip, port=self.port, kademlia_server=self)
        self.listener.start()

        self.server = Server()
        self.loopThread = Thread(target=self.start_server)
        self.loopThread.start()

    def start_server(self):
        handler = logging.FileHandler('log_kademlia.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        log = logging.getLogger('kademlia')
        log.addHandler(handler)
        log.setLevel(logging.DEBUG)

        self.loop.set_debug(True)
        self.loop.run_until_complete(self.server.listen(self.port))

        # Testing purposes (hard-coded)
        bootstrap_node = [("127.0.0.1", 6000)]
        self.loop.run_until_complete(self.server.bootstrap(bootstrap_node))

        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.server.stop()

    def close_server(self):
        self.loop.call_soon_threadsafe(self.loop.stop)

    async def get_timeline_from_follower(self, followed_username, followed_timestamp):
        follow_response = await self.server.get(followed_username)
        if follow_response is not None:
            follow_data = json.loads(follow_response)
            message_content = {'msg_type': 'GET',
                            'timestamp': followed_timestamp}
            request_response = await make_connection(
                    follow_data['ip'], follow_data['port'], message_content)
            return request_response
        else:
            print_log(f"Username {followed_username} doesn\'t exist.")

    async def get_timeline(self, username):
        try:
            response = await self.server.get(username)

            if response is not None:
                data = json.loads(response)
                # [{"username": followed_username, "last_msg_timestamp": last_timestamp, "messages": [[content, timestamp]], "ACK:": 1}]
                following = data['following']

                tasks = [self.get_timeline_from_follower(
                    followed_data["username"], followed_data["last_msg_timestamp"]) for followed_data in following]
                timeline = await asyncio.gather(*tasks)
                for msgs, follower in zip(timeline, following):
                    timeline.append(copy.deepcopy(follower["messages"]))
                    follower['messages'].extend(msgs)
                    _, highest_timestamp = max(msgs, key=lambda item: item[1])
                    follower['last_msg_timestamp'] = highest_timestamp

                await self.server.set(username, json.dumps(data))
                return timeline 
            else:
                print_log(f"Username {username} doesn\'t exist.")
        except Exception as err:
            print_log(err)


    # async def check_want_to_follow(self):
    #     response = await self.server.get(f"{self.username}-want_to_follow")

    #     if response is not None:
    #         usernames = 
    #     else:
    #         return

    # Executed every time the node gets online. 
    # The node checks the followers state and if present in the "pending_unfollow" state of each follower it signals the follower to remove him.
    async def check_unfollow_status(self):
        response = await self.server.get(self.username)
        
        if response is not None:
            my_data = json.loads(response)
            followers = my_data["followers"]
            to_add = []
            tasks = []

            for follower_username in followers:
                follower_data = json.loads(await self.server.get(follower_username))
                temp_unfollow = follower_data["pending_unfollow"]
                if self.username in temp_unfollow:
                    message = {"msg_type": "ACK_UNFOLLOW", "username": self.username}
                    tasks.append(make_connection(follower_data["ip"], follower_data["port"], message))
                else:
                    to_add.append(follower_username) 

            await asyncio.gather(*tasks)

            my_data["followers"] = to_add

            await self.server.set(self.username, json.dumps(my_data))

        else:
            print_log(f"Username {self.username} doesn\'t exist.")

    async def network_login(self, username, plain_password):
        response = await self.server.get(username)

        if response is not None:
            user_state = json.loads(response)
            hashed_password = sha256(
                plain_password.encode('utf-8')).hexdigest()

            if user_state['password'] != hashed_password:
                print_log(f"Incorrect password for user {username}.")
                return False

            need_to_set = False

            if user_state['port'] != self.port:
                user_state['port'] = self.port
                need_to_set = True

            if user_state['ip'] != self.ip:
                user_state['ip'] = self.ip
                need_to_set = True

            if need_to_set:
                await self.server.set(username, json.dumps(user_state))

            self.username = username

            await self.check_unfollow_status()

            return True
        else:
            print_log(f"Username {username} doesn\'t exist.")
            return False

    async def network_register(self, username, plain_password):
        response = await self.server.get(username)

        if response is None:
            hashed_password = sha256(
                plain_password.encode('utf-8')).hexdigest()

            user_state = {}
            user_state['password'] = hashed_password
            user_state['followers'] = []
            user_state['following'] = []
            user_state['pending_unfollow'] = []
            user_state['messages'] = []
            user_state['ip'] = self.ip
            user_state['port'] = self.port

            self.username = username

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
            data["messages"].append([message, get_time()])
            Screen.println("\n\nWriting to the network...")
            await self.server.set(username, json.dumps(data))

    async def add_following(self, my_username, username_to_follow):
        if my_username == username_to_follow:
            Screen.println("You cannot follow yourself!")
            return False

        response = await self.server.get(my_username)

        if response is None:
            print_log(f"Username {my_username} does not exist.")
        else:
            Screen.println(f"\n\nFollowing {username_to_follow}...\n")

            data = json.loads(response)

            users_following = [user_data["username"]
                                for user_data in data["following"]]
            if not username_to_follow in users_following:
                # [{"username": followed_username, "last_msg_timestamp": last_timestamp, "messages": [[content, timestamp]], "ACK:": 1}]

                response = await self.server.get(username_to_follow)
                followed_data = json.loads(response)
                message_content = {'msg_type': 'FOLLOW',
                                    'following': my_username}
                followed_response = await make_connection(
                    followed_data['ip'], followed_data['port'], message_content)

                print_log("Follow response: " + str(followed_response))
                following_ack = followed_response if followed_response is not None else "NOT_ONLINE_FOLLOW"
                data["following"].append(
                    {"username": username_to_follow, "last_msg_timestamp": "", "messages": [], "ACK": following_ack["msg_type"]})
                await self.server.set(my_username, json.dumps(data))
            else:
                print_log(f"You already follow {username_to_follow}.")

    async def remove_following(self, my_username, username_to_unfollow):
        if my_username == username_to_unfollow:
            Screen.println("You cannot unfollow yourself!")
            return False

        response = await self.server.get(my_username)

        if response is None:
            print_log(f"Username {my_username} does not exist.")
        else:
            Screen.println(f"\n\nUnfollowing {username_to_unfollow}...\n")

            data = json.loads(response)

            users_following = [user_data["username"]
                                for user_data in data["following"]]
            if username_to_unfollow in users_following:
                # [{"username": followed_username, "last_msg_timestamp": last_timestamp, "messages": [[content, timestamp]], "ACK:": 1}]

                response = await self.server.get(username_to_unfollow)
                followed_data = json.loads(response)
                message_content = {'msg_type': 'UNFOLLOW',
                                    'unfollowing': my_username}
                unfollowed_response = await make_connection(
                    followed_data['ip'], followed_data['port'], message_content)

                for follow in data["following"]:
                    if follow["username"] == username_to_unfollow:
                        data["following"].remove(follow)
                        break
                
                if unfollowed_response is None:
                    data["pending_unfollow"].append(username_to_unfollow)                
                
                await self.server.set(my_username, json.dumps(data))
            else:
                print_log(f"You are not following {username_to_unfollow}.")

    async def get_info(self):
        response = await self.server.get(self.username)

        if response is None:
            print_log(f"Username {self.username} does not exist.")
        else:
            return json.loads(response)
