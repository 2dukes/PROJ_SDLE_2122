from consolemenu import *
from consolemenu.items import *
from login import login
from register import register

menu = ConsoleMenu(title="================== Decentralized Timeline ==================", subtitle="Please Register or Login:")

login_option = FunctionItem("Login", login, [])
register_option = FunctionItem("Register", register, [])

menu.append_item(register_option)
menu.append_item(login_option)

menu.show()
