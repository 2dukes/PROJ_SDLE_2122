from utils import *
from node.node import Node
from node.kademliaServer import KademliaServer
from consolemenu.screen import Screen
from consolemenu.items import *
from consolemenu import *
import sys
import asyncio
from operator import itemgetter
import signal
import os
import time
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.append(parentdir)


def view_timeline(kademlia_server, username):
    timeline = asyncio.run(kademlia_server.get_timeline(username))

    print_log(str(timeline))


def follow_user(kademlia_server, username):
    username_to_follow = input("\nPlease enter the username to follow: ")
    asyncio.run(kademlia_server.add_following(username, username_to_follow))
    input("\nPress ENTER to continue...\n")


def unfollow_user(kademlia_server, username):
    pass


def search():
    pass


def view_info(kademlia_server, username):
    data = asyncio.run(kademlia_server.get_info())
    print_log(str(data))

    if (data is None):
        Screen.println("\nNo data is available...")
    else:
        Screen.println(
            f"=============== {username}\'s data: =============== ")
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

    kademlia_server, loop, port = itemgetter(
        'server', 'loop', 'port')(server_config)
    server = kademlia_server.server

    #node = Node(username=username, ip="localhost", port=port+1, server=server, loop=loop)

    # if (is_bootstrap_node):
    #     await server.set("username", username)
    # else:
    #     print_log(await server.get("username"))

    auth_menu = ConsoleMenu(title="================== Decentralized Timeline ==================",
                            subtitle=f"Hello, {username}", show_exit_option=False)

    view_timeline_option = FunctionItem("View Timeline", view_timeline, [
                                        kademlia_server, username])
    publish_msg = FunctionItem("Publish Message", publish, [
                               kademlia_server, username])
    follow_user_item = FunctionItem("Follow a user", follow_user, [
                                    kademlia_server, username])
    unfollow_user_item = FunctionItem("Unfollow a user", unfollow_user, [
                                      kademlia_server, username])
    search_content_item = FunctionItem("Search for content", search)
    view_info_item = FunctionItem("View My Info", view_info, [
                                  kademlia_server, username])
    logout_item = FunctionItem("Logout", logout, [kademlia_server])

    auth_menu.append_item(view_timeline_option)
    auth_menu.append_item(publish_msg)
    auth_menu.append_item(follow_user_item)
    auth_menu.append_item(unfollow_user_item)
    auth_menu.append_item(search_content_item)
    auth_menu.append_item(view_info_item)
    auth_menu.append_item(logout_item)

    auth_menu.show()
