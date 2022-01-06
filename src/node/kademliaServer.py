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
            my_messages = follow_data["messages"]

            request_response = list(
                filter(lambda x: x[1] > followed_timestamp, my_messages))

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
                users_following = [user_data["username"] for user_data in data["following"]]
                pending_unfollow = data["pending_unfollow"]
                
                users_following = list(filter(lambda x: x not in pending_unfollow, users_following))
                following_data = [x for x in following if x['username'] in users_following]

                print_log(following_data)
                
                tasks = [self.get_timeline_from_follower(
                    followed_data["username"], followed_data["last_msg_timestamp"]) for followed_data in following_data]

                timeline = await asyncio.gather(*tasks)
                print_log(timeline)
                for msgs, follower in zip(timeline, following):
                    timeline.append(copy.deepcopy(follower["messages"]))
                    if len(msgs) > 0:
                        follower['messages'].extend(msgs)
                        _, highest_timestamp = max(msgs, key=lambda item: item[1])
                        follower['last_msg_timestamp'] = highest_timestamp
                
                await self.server.set(username, json.dumps(data))
                return timeline 
            else:
                print_log(f"Username {username} doesn\'t exist.")
        except Exception as err:
            print_log(err)
            

    

    # username_offline_wants_to_follow = [username1, username2]

    # get(username_offline_wants_to_follow) => follow cada um => ack_follow => elimina username1
    
    # se o outro nó mudasse o nosso estado, poderiam haver conflitos
    # (vários nós a tentar mudar o nosso estado)
    async def check_pending_followers(self):
        responses = asyncio.gather(self.server.get(f"{self.username}-pending_followers"), self.server.get(self.username)) #need to make sure users are added to the pending_followers list when a user fails to follow another

        if responses[0] is not None:
            usernames = json.loads(responses[0])
            my_data = json.loads(responses[1])
            # user_data_retrieval_tasks = []

            # for user in usernames:
            #     user_data_retrieval_tasks.append(self.server.get(user))

            # users_data = asyncio.gather(*user_data_retrieval_tasks)

            tasks = []

            my_data["followers"].extend(usernames)
            
            # for user_data in users_data:
            #     user = json.loads(user_data)
            #     my_data["followers"].append(user["username"])
                # tasks.append(make_connection(user["ip"], user["port"], {"msg_type": "ACK_FOLLOW", "username": self.username})) # where is this processed on the other side?

            tasks.append(self.server.set(self.username, json.dumps(my_data)))
            tasks.append(self.server.set(f"{self.username}-pending_followers", json.dumps([])))
            
            await asyncio.gather(*tasks)            

        else:
            return

    # Executed every time the node gets online. 
    # The node checks the followers state and if present in the "pending_unfollow" state of each follower it signals the follower to remove him.
    async def check_unfollow_status(self, my_data):        
        followers = my_data["followers"]
        remaining_followers = []
        to_remove = []
        tasks = []

        for follower_username in followers:
            follower_data = json.loads(await self.server.get(follower_username))
            temp_unfollow = follower_data["pending_unfollow"]
            if self.username in temp_unfollow:
                message = {"msg_type": "ACK_UNFOLLOW", "username": self.username}
                tasks.append(make_connection(follower_data["ip"], follower_data["port"], message))
                to_remove.append(follower_username) 
            else:
                remaining_followers.append(follower_username) 

        result = await asyncio.gather(*tasks)
        
        # Remaining followers are only the ones that are online.
        for idx in range(len(result)):
            if result[idx] is None:
                remaining_followers.append(to_remove[idx])

        my_data["followers"] = remaining_followers

        await self.server.set(self.username, json.dumps(my_data))


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

            await self.check_unfollow_status(user_state)
            # await self.check_pending_followers()

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

                data["following"].append(
                    {"username": username_to_follow, "last_msg_timestamp": "", "messages": []})

                if followed_response is None:
                    tasks = []

                    pending_followers = f"{username_to_follow}-pending_followers"

                    tasks.append(self.server.set(my_username, json.dumps(data)))
                    tasks.append(self.server.get(pending_followers))
                    responses = await asyncio.gather(*tasks)
                    
                    if responses[1] is None:
                        await self.server.set(pending_followers, json.dumps([self.username]))
                    else:
                        current_list = json.loads(responses[1])
                        current_list.append(self.username)
                        await self.server.set(pending_followers, json.dumps(current_list))
                else:
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
