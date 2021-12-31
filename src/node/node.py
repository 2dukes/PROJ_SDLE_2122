from threading import *
from consolemenu import Screen
import asyncio
import json
import time

from utils import print_log

class Node:
    def __init__(self, username, ip, port, server, loop):
        self.username = username
        self.ip = ip
        self.port = port
        self.server = server

        # Get from Kademlia network
        self.followers = []
        self.following = []
        self.messages = []

        self.loop = loop

        self.update_thread = Thread(target=self.update_server)
        self.update_thread.start()

    async def add_follower(self, username):
        if username == self.username:
            Screen.println("You cannot follow yourself")
            return False

        if username not in self.followers:
            Screen.println("You already follow this user")
            return False

        if username not in self.followers and data:
            return False

    def remove_follower(self, username):
        if username in self.followers:
            self.followers.remove(username)
    
    def add_following(self, username):
        if username not in self.following:
            self.following.append(username)

    def remove_following(self, username):
        if username in self.following:
            self.following.remove(username)
    
    def update_server(self):
        while True:
            asyncio.run(self.write_to_server())
            time.sleep(5)

    async def write_to_server(self):
        response = await self.server.get(self.username)
        data = json.loads(response)
        data["followers"] = self.followers
        data["following"] = self.following
        data["messages"] = self.messages
        await self.server.set(self.username, json.dumps(data))

