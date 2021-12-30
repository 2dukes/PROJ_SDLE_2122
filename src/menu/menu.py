from consolemenu import *
from consolemenu.items import *
from login import login
from register import register
import sys

if __name__ == "__main__":
    is_bootstrap_node = len(sys.argv) > 1 and (sys.argv[1] == "-b" or sys.argv[1] == "--bootstrap")

    menu = ConsoleMenu(title="================== Decentralized Timeline ==================", subtitle="Please Register or Login:")

    login_option = FunctionItem("Login", login, [is_bootstrap_node])
    register_option = FunctionItem("Register", register, [is_bootstrap_node])

    menu.append_item(register_option)
    menu.append_item(login_option)

    menu.show()
