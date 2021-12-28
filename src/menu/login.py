from consolemenu import Screen
from consolemenu import *
from consolemenu.items import *
from authenticated import authenticated

def login():
    username = input("Username: ")
    password = input("Password: ")
    
    while (not check_credentials(username, password)):    
        Screen.println("\nInvalid username or password! Please try again")
        Screen.println("\n-----------------------------------------------\n")
        username = input("Username: ")
        password = input("Password: ")

    authenticated(username)

def check_credentials(username, password):
    return (username == "admin" and password == "admin")
