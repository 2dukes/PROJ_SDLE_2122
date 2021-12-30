import os
from time import sleep
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.append(parentdir)

from operator import itemgetter
import asyncio
from consolemenu import *
from consolemenu.items import *
from node.kademliaServer import KademliaServer
from node.node import Node

from utils import *


def view_timeline():
    # get timeline from network

    """
    timeline = [
        {
            "username": "test",
            "message": "This is the message",
            "timestamp": "2021-12-01:12h-30m:30s" # use correct format
        },
        {
            "username": "test",
            "message": "This is the message",
            "timestamp": "2021-12-01:12h-30m:30s" # use correct format
        },
        {
            "username": "test",
            "message": "This is the message",
            "timestamp": "2021-12-01:12h-30m:30s" # use correct format
        },
        {
            "username": "test",
            "message": "This is the message",
            "timestamp": "2021-12-01:12h-30m:30s" # use correct format
        },
        {
            "username": "test",
            "message": "This is the message",
            "timestamp": "2021-12-01:12h-30m:30s" # use correct format
        }
    ]
    """

    pass

def follow_user():
    pass

def unfollow_user():
    pass

def search():
    pass

def view_info():
    with open("local_data.json", "r") as data_file:
        data = {} # get from network
        # data = dict(get(username))
        # followers = data["followers"]
        # following = data["following"]
        # address = data["address"]
        # port = data["port"]
        Screen.println(str(data)) # can we print a dictionary?



def publish():
    message = input("Please write the content of your message: ")
    # send message to network
    pass

def logout():
    #...
    #login()
    pass



async def authenticated(username, is_bootstrap_node, server_config):

    server, loop, port = itemgetter('server', 'loop', 'port')(server_config)

    node = Node(username=username, ip="localhost", port=port+1, server=server, loop=loop)

    
    if (is_bootstrap_node):
        await server.set("username", username)
    else:
        print_log(await server.get("username"))


    auth_menu = ConsoleMenu(title="================== Decentralized Timeline ==================", subtitle=f"Hello, {username}", show_exit_option=False)

    view_timeline_option = FunctionItem("View Timeline", view_timeline)
    publish_msg = FunctionItem("Publish Message", publish)
    follow_user_item = FunctionItem("Follow a user", follow_user)
    unfollow_user_item = FunctionItem("Unfollow a user", unfollow_user)
    search_content_item = FunctionItem("Search for content", search)
    view_info_item = FunctionItem("View My Info", view_info)
    logout_item = ExitItem("Logout", logout)

    auth_menu.append_item(view_timeline_option)
    auth_menu.append_item(publish_msg)
    auth_menu.append_item(follow_user_item)
    auth_menu.append_item(unfollow_user_item)
    auth_menu.append_item(search_content_item)
    auth_menu.append_item(view_info_item)
    auth_menu.append_item(logout_item)

    auth_menu.show()
