from consolemenu import Screen
from consolemenu import *
from consolemenu.items import *
import asyncio
from authenticated import authenticated
from node.create_server import create_server

def login(is_bootstrap_node):
    kademlia_server = create_server(is_bootstrap_node)

    username = input("Username: ")
    password = input("Password: ")

    Screen.println("\nChecking credentials...\n")
    
    while not asyncio.run(kademlia_server.network_login(username, password)):
        Screen.println("\nInvalid username or password! Please try again...")
        Screen.println("\n-----------------------------------------------\n")
        username = input("Username: ")
        password = input("Password: ")

    asyncio.run(authenticated(username, kademlia_server))
