from threading import *

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

        # self.timelineThread = Thread(target=self.updateTimeline)
        #self.timelineThread.start()

    def addFollower(self, username):
        if username not in self.followers:
            self.followers.append(username)

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
        while (True):
            # Get data from network and update timeline data
            pass

    def writeToTimeline(self):
        # Write to the network
        pass
