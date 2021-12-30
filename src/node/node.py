from threading import *
from consolemenu import Screen
import asyncio

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

        self.loop = loop

        self.timelineThread = Thread(target=self.updateTimeline)
        self.timelineThread.start()

    async def addFollower(self, username):
        if username == self.username:
            Screen.println("You cannot follow yourself")
            return False

        if username not in self.followers:
            Screen.println("You already follow this user")
            return False

        if username not in self.followers and username != self.username:
            self.followers.append(username)

        return False

    def removeFollower(self, username):
        if username in self.followers:
            self.followers.remove(username)
    
    def addFollowing(self, username):
        if username not in self.following:
            self.following.append(username)

    def removeFollowing(self, username):
        if username in self.following:
            self.following.remove(username)
    
    def updateTimeline(self):
        pass
        # data = await self.server.get(self.username)
        # while True:
        #     self.followers = data["followers"]
        #     self.following = data["following"]

    async def writeToTimeline(self):
        data = await self.server.get(self.username)
        while True:
            data["followers"] = self.followers
            data["following"] = self.following
            await self.server.set(self.username, data)

