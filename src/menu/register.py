from consolemenu import Screen
from consolemenu import *
from consolemenu.items import *
from authenticated import authenticated

def register():
    username = input("Username: ")
    password = input("Password: ")
    
    while (not check_valid_credentials(username, password)):    
        Screen.println("\nInvalid username or password! Please try again")
        Screen.println("\n-----------------------------------------------\n")
        username = input("Username: ")
        password = input("Password: ")

    authenticated(username)

def username_exists(username):
    return username == "admin"

def check_valid_credentials(username, password):
    return password != "" and not username_exists(username)

