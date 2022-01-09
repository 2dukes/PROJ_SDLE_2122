import logging
import asyncio
import json
import datetime

from consolemenu import Screen
from node.polling import PollingFollowing
from utils import get_time, get_time_to_compare

from kademlia.network import Server
from threading import *
from utils import make_connection
from hashlib import sha256
from os import getenv
from node.listener import Listener

class KademliaServer:
    def __init__(self, ip, port, loop):
        self.ip = ip
        self.port = port
        self.loop = loop

        self.listener = Listener(
            ip=self.ip, port=self.port, kademlia_server=self)
        self.listener.start()

        self.server = Server()
        self.loopThread = Thread(target=self.start_server)
        self.loopThread.start()

        self.logger = logging.getLogger(f"Node {str(self.server.node.long_id)}")
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler('logfile.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)

        self.log_info(f"ENTERING (ip={self.ip}, port={self.port})")

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
        
        bootstrap_node = [(getenv('BOOTSTRAP_IP'), int(getenv('BOOTSTRAP_PORT')))]
        self.loop.run_until_complete(self.server.bootstrap(bootstrap_node))

        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.server.stop()

    def close_server(self):
        self.loop.call_soon_threadsafe(self.loop.stop)

    async def get_timeline_from_follower(self, followed_username, followed_timestamp, timestamp_to_compare):
        follow_response = await self.server.get(followed_username)

        if follow_response is not None:
            follow_data = json.loads(follow_response)            
            follower_messages = follow_data["messages"] # {"messages": [[content, timestamp]]}
            results = []

            for msg in reversed(follower_messages):
                aux_msg = msg.copy()
                aux_msg.append(followed_username)

                # If it's ephemeral, and it was read, filter it (remove it)
                if msg[1] <= followed_timestamp and msg[1] >= timestamp_to_compare:
                    aux_msg.append("read")
                elif msg[1] > followed_timestamp:
                    aux_msg.append("unread")
                elif msg[1] < timestamp_to_compare:
                    break

                results.append(aux_msg)

            return results
        else:
            self.log_info(f"View Timeline [Follower]- Username {followed_username} doesn\'t exist.", level="ERROR")

    async def get_timeline(self, username):
        try:
            response = await self.server.get(username)

            if response is not None:
                data = json.loads(response)                 
                following = data['following'] # [{"username": followed_username, "last_msg_timestamp": last_timestamp, "messages": [[content, timestamp]]}]
                users_following = [user_data["username"]
                                   for user_data in data["following"]]
                pending_unfollow = data["pending_unfollow"]

                users_following = list(
                    filter(lambda x: x not in pending_unfollow, users_following))
                following_data = [
                    x for x in following if x['username'] in users_following]

                self.log_info(f"View Timeline [Following] - {str(following_data)}")

                timestamp_to_compare = get_time_to_compare()
                tasks = [self.get_timeline_from_follower(
                    followed_data["username"], followed_data["last_msg_timestamp"], timestamp_to_compare) for followed_data in following_data]

                timeline = await asyncio.gather(*tasks)
                
                self.log_info(f"View Timeline - {str(timeline)}")

                for msgs, follower in zip(timeline, following):
                    if len(msgs) > 0:
                        _, highest_timestamp, _, _ = max(
                            msgs, key=lambda item: item[1])
                        follower['last_msg_timestamp'] = highest_timestamp

                await self.server.set(username, json.dumps(data))
                return timeline
            else:
                self.log_info(f"View Timeline - Username {username} doesn\'t exist.", level="ERROR")
        except Exception as err:
            self.log_info(f"View Timeline - {str(err)}", level="ERROR")

    # Check pending followers whenever node wake up from offline state.
    # Need to make sure users are added to the pending_followers list when a user fails to follow another.
    async def check_pending_followers(self):
        responses = await asyncio.gather(self.server.get(f"{self.username}-pending_followers"), self.server.get(self.username))

        if responses[0] is not None:
            usernames = json.loads(responses[0])
            my_data = json.loads(responses[1])
            
            log_usernames = ", ".join(usernames)
            self.log_info(f"Checking Pending Followers - {log_usernames}")

            tasks = []

            my_data["followers"].extend(usernames)

            tasks.append(self.server.set(self.username, json.dumps(my_data)))
            tasks.append(self.server.set(
                f"{self.username}-pending_followers", json.dumps([])))

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

        log_usernames = ", ".join(followers)
        self.log_info(f"Checking Unfollowers (Pending)- {log_usernames}")

        for follower_username in followers:
            follower_data = json.loads(await self.server.get(follower_username))
            temp_unfollow = follower_data["pending_unfollow"]
            if self.username in temp_unfollow:
                message = {"msg_type": "ACK_UNFOLLOW",
                           "username": self.username}
                tasks.append(make_connection(
                    follower_data["ip"], follower_data["port"], message))
                to_remove.append(follower_username)
            else:
                remaining_followers.append(follower_username)

        result = await asyncio.gather(*tasks)

        # Remaining followers are only the ones that are online.
        for idx in range(len(result)):
            if result[idx] is None:
                remaining_followers.append(to_remove[idx])

        my_data["followers"] = remaining_followers

        log_usernames = ", ".join(remaining_followers)
        self.log_info(f"Checking Unfollowers (Remaining)- {log_usernames}")

        await self.server.set(self.username, json.dumps(my_data))

    async def network_login(self, username, plain_password):
        response = await self.server.get(username)

        if response is not None:
            user_state = json.loads(response)
            hashed_password = sha256(
                plain_password.encode('utf-8')).hexdigest()

            if user_state['password'] != hashed_password:
                self.log_info(f"Login - Incorrect password for user {username}.", level="ERROR")
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
            await self.check_pending_followers()

            self.log_info("Login - Successful.")
            return True
        else:
            self.log_info(f"Login - Username {username} doesn\'t exist.", level="ERROR")
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
            
            self.log_info("Register - Successful.")
            return True
        else:
            self.log_info(f"Register - Username {username} already exists.", level="ERROR")
            return False

    async def publish(self, message, username):
        response = await self.server.get(username)
        if response is None:
            self.log_info(f"Publish Message - Username {username} does not exist.", level="ERROR")
        else:
            data = json.loads(response)
            data["messages"].append([message, get_time()])
            Screen.println("\n\nWriting to the network...")
            await self.server.set(username, json.dumps(data))
            self.log_info(f"Publish Message - {message}.")

    async def add_following(self, my_username, username_to_follow):
        if my_username == username_to_follow:
            Screen.println("You cannot follow yourself!")
            return False

        response = await self.server.get(my_username)

        if response is None:
            self.log_info(f"Add Following - Username {my_username} does not exist.", level="ERROR")
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

                self.log_info(f"Add Following - Following {username_to_follow}.")

                data["following"].append(
                    {"username": username_to_follow, "last_msg_timestamp": str(datetime.datetime(1970, 1, 1))})

                if followed_response is None:
                    self.log_info(f"Add Following - Inserting {username_to_follow} in pending_followers.")
                    poolFollow = PollingFollowing(self, username_to_follow)
                    poolFollow.daemon = True
                    poolFollow.start()

                await self.server.set(my_username, json.dumps(data))
            else:
                Screen.println(f"You already follow {username_to_follow}.")

    async def remove_following(self, my_username, username_to_unfollow):
        if my_username == username_to_unfollow:
            Screen.println("You cannot unfollow yourself!")
            return False

        response = await self.server.get(my_username)

        if response is None:
            self.log_info(f"Remove Following - Username {my_username} does not exist.", level="ERROR")
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
                
                self.log_info(f"Remove Following - Unfollowing {username_to_unfollow}.")

                if unfollowed_response is None:
                    self.log_info(f"Remove Following - Inserting {username_to_unfollow} in pending_unfollow.")
                    data["pending_unfollow"].append(username_to_unfollow)

                await self.server.set(my_username, json.dumps(data))
            else:
                Screen.println(f"You are not following {username_to_unfollow}.")

    async def search_users(self, query):
        data = await self.get_info("registered_usernames")
        self.log_info(f"Search User - User {query}.")

        return [username for username in data if query in username]

    async def search_content(self, query):
        data = await self.get_info("registered_usernames")
        self.log_info(f"Search Content - Content {query}.")

        results = []

        for username in data:
            user_data = await self.get_info(username)
            user_messages = user_data["messages"]
            for message in user_messages:
                if query in message[0]:
                    results.append((message, username))

        filtered_results = []
        timestamp_to_compare = get_time_to_compare()
        for result in results:
            timestamp = result[0][1]
            if result[1] == self.username or timestamp >= timestamp_to_compare:
                filtered_results.append(result)

        return filtered_results

    async def get_info(self, key):
        response = await self.server.get(key)

        if response is None:
            self.log_info(f"GET INFO - Key {key} does not exist.", level="ERROR")
        else:
            return json.loads(response)
    
    def log_info(self, msg, level="DEBUG"):
        if level == "DEBUG":
            self.logger.debug(msg)
        elif level == "ERROR":
            self.logger.error(msg)
