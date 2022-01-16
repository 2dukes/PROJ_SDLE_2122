from consolemenu import Screen
from consolemenu import *
from consolemenu.items import *
import asyncio
import os
from authenticated import authenticated
from node.create_server import create_server
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.append(parentdir)
from node.polling import PollingExistingUsernames
from utils import *


def register(is_bootstrap_node):
    kademlia_server = create_server(is_bootstrap_node)

    username = input("Username: ")
    password = get_valid_password()

    Screen.println("\nMaking registration...\n")
    
    while not asyncio.run(kademlia_server.network_register(username, password)):
        Screen.println("\nInvalid username! Please choose another one...")
        Screen.println("\n-----------------------------------------------\n")
        username = input("Username: ")
        password = input("Password: ")

    polling_all_users = PollingExistingUsernames(kademlia_server)
    polling_all_users.daemon = True
    polling_all_users.start()
    
    Screen.println("Logging in...")

    asyncio.run(authenticated(username, kademlia_server))
