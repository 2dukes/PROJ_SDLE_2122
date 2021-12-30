from consolemenu import Screen
from consolemenu import *
from consolemenu.items import *
import asyncio
from authenticated import authenticated
from node.create_server import create_server

def login(is_bootstrap_node):
    server_config = create_server(is_bootstrap_node)
    server = server_config["server"]

    username = input("Username: ")
    password = input("Password: ")

    Screen.println("\nChecking credentials...\n")
    
    while not asyncio.run(server.network_login(username, password)):
        Screen.println("\nInvalid username or password! Please try again...")
        Screen.println("\n-----------------------------------------------\n")
        username = input("Username: ")
        password = input("Password: ")

    asyncio.run(authenticated(username, is_bootstrap_node, server_config))
