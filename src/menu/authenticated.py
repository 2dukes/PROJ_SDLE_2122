import os
import time
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.append(parentdir)

import signal
from operator import itemgetter
import asyncio
import sys
from consolemenu import *
from consolemenu.items import *
from node.kademliaServer import KademliaServer
from node.node import Node

from utils import *


def view_timeline():
    # get timeline from network

   

    pass

def follow_user(kademlia_server, username):
    username_to_follow = input("Please enter the username to follow: ")
    asyncio.run(kademlia_server.add_following(username, username_to_follow))
    input("\nPress ENTER to continue...\n")

def unfollow_user(kademlia_server, username):
    pass

def search():
    pass

def view_info(kademlia_server, username):
    data = asyncio.run(kademlia_server.get_info(username))

    if (data is None):
        Screen.println("\nNo data is available...")
    else:
        Screen.println(f"=============== {username}\'s data: =============== ")
        Screen.println()
        Screen.println("Followers: " + str(data["followers"]))
        Screen.println("Following: " + str(data["following"]))
        Screen.println("Messages: " + str(data["messages"]))
        
    input("\nPress ENTER to continue...\n")

def publish(kademlia_server, username):
    message = input("Please write the content of your message: ")
    asyncio.run(kademlia_server.publish(message, username))
    input("\nPress ENTER to continue...\n")

def logout(kademlia_server):
    pid = os.getpid()
    os.kill(pid, signal.SIGINT)
    # kademlia_server.close_server()
    # sys.exit()

async def authenticated(username, is_bootstrap_node, server_config):

    kademlia_server, loop, port = itemgetter('server', 'loop', 'port')(server_config)
    server = kademlia_server.server

    #node = Node(username=username, ip="localhost", port=port+1, server=server, loop=loop)
    
    # if (is_bootstrap_node):
    #     await server.set("username", username)
    # else:
    #     print_log(await server.get("username"))

    auth_menu = ConsoleMenu(title="================== Decentralized Timeline ==================", subtitle=f"Hello, {username}", show_exit_option=False)

    view_timeline_option = FunctionItem("View Timeline", view_timeline)
    publish_msg = FunctionItem("Publish Message", publish, [kademlia_server, username])
    follow_user_item = FunctionItem("Follow a user", follow_user, [kademlia_server, username])
    unfollow_user_item = FunctionItem("Unfollow a user", unfollow_user, [kademlia_server, username])
    search_content_item = FunctionItem("Search for content", search)
    view_info_item = FunctionItem("View My Info", view_info, [kademlia_server, username])
    logout_item = FunctionItem("Logout", logout, [kademlia_server])

    auth_menu.append_item(view_timeline_option)
    auth_menu.append_item(publish_msg)
    auth_menu.append_item(follow_user_item)
    auth_menu.append_item(unfollow_user_item)
    auth_menu.append_item(search_content_item)
    auth_menu.append_item(view_info_item)
    auth_menu.append_item(logout_item)

    auth_menu.show()
