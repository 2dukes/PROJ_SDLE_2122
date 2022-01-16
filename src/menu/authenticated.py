from utils import *
from consolemenu.screen import Screen
from consolemenu.items import *
from consolemenu import *
import asyncio
from operator import itemgetter
import signal
from hashlib import sha256
import os
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.append(parentdir)


def view_timeline(kademlia_server):
    timeline = asyncio.run(
        kademlia_server.get_timeline(kademlia_server.username))
    # [[['hello', '2022-01-05 16:22:08.818028+00:00']], [['bye', '2021-05-03 18:02:08.818028+00:00']]]
    
    flat_list = []
    for follower in timeline:
        for message in follower:
            flat_list.append(message)

    user_state = asyncio.run(
        kademlia_server.server.get(kademlia_server.username))
    state = json.loads(user_state)

    flat_list.extend(state["messages"])
    sorted_entries = sorted(flat_list, key=itemgetter(1), reverse=True)
    kademlia_server.log_info(f"View Timeline (All Messages) - {str(sorted_entries)}")

    print("____________________________________________________________________________\n")
    print("     Timestamp      |     Status     |      User      |      Message")
    print("____________________________________________________________________________\n\n")

    for entry in sorted_entries:
        

        if len(entry)==2:
            entry.append(kademlia_server.username)
            entry.append("N/a")
        entry[0], entry[1], entry[2], entry[3] = entry[1], entry[3], entry[2], entry[0]
        entry[0] = entry[0].split(".")[0]+" |"
        entry[1] = padText(entry[1],14)
        entry[1] += " |"
        entry[2] = padText(entry[2],14)
        entry[2] += " |"
        
        print_with_highlighted_color(f"@{kademlia_server.username}", " ".join(entry))

    input("\nPress ENTER to continue...\n")


def padText(text, len_to_pad):
    if len(text)<len_to_pad:
        i = len(text)
        while i < len_to_pad:
            text+= " "
            i+=1
    return text

def follow_user(kademlia_server):
    username_to_follow = input("\nPlease enter the username to follow: ")
    asyncio.run(kademlia_server.add_following(
        kademlia_server.username, username_to_follow))
    input("\nPress ENTER to continue...\n")


def unfollow_user(kademlia_server):
    username_to_unfollow = input("\nPlease enter the username to unfollow: ")
    asyncio.run(kademlia_server.remove_following(
        kademlia_server.username, username_to_unfollow))
    input("\nPress ENTER to continue...\n")


def search_users(kademlia_server):
    query = input("\nPlease enter you query: ")
    returned_users = asyncio.run(kademlia_server.search_users(query))

    print()
    for user in returned_users:
        print_with_highlighted_color(query, f"  - {user}")

    input("\nPress ENTER to continue...\n")


def search_content(kademlia_server):
    query = input("\nPlease enter you query: ")
    results = asyncio.run(kademlia_server.search_content(query))

    Screen.printf("______________________________________________________________________________________\n")
    Screen.printf("                                   |                          |                       \n")
    Screen.printf("   Timestamp                       |   User                   |   Message             \n")
    Screen.printf("___________________________________|__________________________|_______________________\n")
    Screen.printf("                                   |                          |                       \n")

    for message in results:
        Screen.printf(f" {message[0][1]}  | ")
        Screen.printf(padText(message[1], 25))
        Screen.printf("| ")
        print_with_highlighted_color(query, message[0][0])

    # print_with_highlighted_color(query, str(results))
    input("\nPress ENTER to continue...\n")


def search_mentions(kademlia_server):
    results = asyncio.run(kademlia_server.search_content(
        f"@{kademlia_server.username}"))

    Screen.printf("______________________________________________________________________________________\n")
    Screen.printf("                                   |                          |                       \n")
    Screen.printf("   Timestamp                       |   User                   |   Message             \n")
    Screen.printf("___________________________________|__________________________|_______________________\n")
    Screen.printf("                                   |                          |                       \n")

    for message, user in results:
        Screen.printf(f" {message[1]}  | ")
        Screen.printf(padText(user, 25))
        Screen.printf("| ")
        print_with_highlighted_color(f"@{kademlia_server.username}", message[0])

    input("\nPress ENTER to continue...\n")


def view_info(kademlia_server):
    data = asyncio.run(kademlia_server.get_info(kademlia_server.username))
    if (data is None):
        Screen.println("\nNo data is available...")
    else:
        kademlia_server.log_info(f"View Info - {str(data)}")

        Screen.println(
            f"=============== {kademlia_server.username}\'s data: =============== ")
        Screen.println()

        Screen.println("--> Followers:\n")

        if len(data["followers"]) > 0:
            for follower in data["followers"]:
                Screen.println(f"  - {follower}")
        else:
            Screen.println("  Nobody is following you...")

        Screen.println("\n--> Following:\n")

        if len(data["following"]) > 0:
            for following in data["following"]:
                username = following["username"]
                last_msg_timestamp = following["last_msg_timestamp"]
                Screen.println(f" - {username} | Last message timestamp: {last_msg_timestamp}")
        else:
            Screen.println("  You are not following nobody...")

        Screen.println("\n--> Messages:")

        Screen.printf("____________________________________________________________________________\n")
        Screen.printf("                                        |                                   \n")
        Screen.printf("                Timestamp               |      Message                      \n")
        Screen.printf("________________________________________|___________________________________\n")
        Screen.printf("                                        |                                   \n")

        for message in data["messages"]:
            Screen.printf(f" {message[1]}       | ")
            Screen.println(f"{message[0]}")

    input("\nPress ENTER to continue...\n")


def publish(kademlia_server):
    message = input("Please write the content of your message: ")
    asyncio.run(kademlia_server.publish(message, kademlia_server.username))
    input("\nPress ENTER to continue...\n")


def view_all_users(kademlia_server):
    data = asyncio.run(kademlia_server.get_info("registered_usernames"))
    kademlia_server.log_info(f"View All Users - {data}")
    Screen.println("Registered usernames:\n")

    for username in data:
        Screen.println(f"  - {username}")

    input("\nPress ENTER to continue...\n")


def update_password(kademlia_server):

    while True:
        query = input("\nPlease enter your current password: (enter 'menu' to go to the menu) ")
        if (query == "menu"):
            return

        hashed_password = sha256(query.encode('utf-8')).hexdigest()
        my_data = asyncio.run(kademlia_server.get_info(kademlia_server.username))

        if (my_data["password"] == hashed_password):
            break
        else:
            print("Incorrect password!\n")

    plain_password = get_valid_password("\n\nPlease enter you new password: ")
    hashed_password = sha256(plain_password.encode('utf-8')).hexdigest()
    my_data["password"] = hashed_password

    print("\n\nSetting your new password...\n")

    asyncio.run(kademlia_server.server.set(kademlia_server.username, json.dumps(my_data)))

    input("\nPress ENTER to continue...\n")


def logout(kademlia_server):
    kademlia_server.log_info("LEAVING")
    pid = os.getpid()
    os.kill(pid, signal.SIGINT)
    # kademlia_server.close_server()
    # sys.exit()

async def authenticated(username, kademlia_server):
    auth_menu = ConsoleMenu(title="======================= Decentralized Timeline ======================",
                            subtitle=f"Hello, {username}", show_exit_option=False)

    view_timeline_option = FunctionItem(
        "View timeline", view_timeline, [kademlia_server])
    publish_msg = FunctionItem("Publish Message", publish, [kademlia_server])
    follow_user_item = FunctionItem(
        "Follow a user", follow_user, [kademlia_server])
    unfollow_user_item = FunctionItem(
        "Unfollow a user", unfollow_user, [kademlia_server])
    search_users_item = FunctionItem(
        "Search for users", search_users, [kademlia_server])
    search_content_item = FunctionItem(
        "Search for content", search_content, [kademlia_server])
    search_mention_item = FunctionItem(
        "Search for mentions", search_mentions, [kademlia_server])
    view_info_item = FunctionItem("View My Info", view_info, [kademlia_server])
    view_all_users_item = FunctionItem(
        "View all users", view_all_users, [kademlia_server])
    update_password_item = FunctionItem(
        "Update password", update_password, [kademlia_server])
    logout_item = FunctionItem("Logout", logout, [kademlia_server])

    auth_menu.append_item(view_timeline_option)
    auth_menu.append_item(publish_msg)
    auth_menu.append_item(follow_user_item)
    auth_menu.append_item(unfollow_user_item)
    auth_menu.append_item(search_users_item)
    auth_menu.append_item(search_content_item)
    auth_menu.append_item(search_mention_item)
    auth_menu.append_item(view_info_item)
    auth_menu.append_item(view_all_users_item)
    auth_menu.append_item(update_password_item)
    auth_menu.append_item(logout_item)

    auth_menu.show()
