from threading import Thread
import asyncio
import json
import random
from utils import print_log

class PollingExistingUsernames(Thread):
    def __init__(self, kademlia_server):
        super(PollingExistingUsernames, self).__init__()
        self.server = kademlia_server.server
        self.username = kademlia_server.username

    def run(self):
        self.loop = asyncio.new_event_loop()
        self.loop.run_until_complete(self.setup_server())

    async def setup_server(self):
        try:
            successful_check = False

            while not successful_check:
                registered_usernames = await self.server.get("registered_usernames")

                if registered_usernames is not None:
                    registered_usernames = json.loads(registered_usernames)
                    await self.server.set("registered_usernames", json.dumps([*registered_usernames, self.username]))
                else:
                    await self.server.set("registered_usernames", json.dumps([self.username]))

                # CSMA/CD
                await asyncio.sleep(random.uniform(5, 10))

                registered_usernames = json.loads(await self.server.get("registered_usernames"))
                successful_check = self.username in registered_usernames

        except Exception as err:
            print_log(err)

class PollingFollowing(Thread):
    def __init__(self, kademlia_server, want_to_follow):
        super(PollingFollowing, self).__init__()
        self.server = kademlia_server.server
        self.username = kademlia_server.username
        self.want_to_follow = want_to_follow
        self.kademlia_server = kademlia_server

    def run(self):
        self.loop = asyncio.new_event_loop()
        self.loop.run_until_complete(self.setup_server())

    async def setup_server(self):
        try:
            successful_check = False

            key = f"{self.want_to_follow}-pending_followers"

            while not successful_check:
                current_list = await self.kademlia_server.get_info(key)

                if current_list is not None:
                    current_list.append(self.username)
                    await self.server.set(key, json.dumps(current_list))
                else:
                    await self.server.set(key, json.dumps([self.username]))

                # CSMA/CD
                await asyncio.sleep(random.uniform(5, 10))

                current_list = await self.kademlia_server.get_info(key)
                successful_check = self.username in current_list

        except Exception as err:
            print_log(err)
