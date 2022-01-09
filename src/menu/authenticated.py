from utils import *
from consolemenu.screen import Screen
from consolemenu.items import *
from consolemenu import *
import asyncio
from operator import itemgetter
import signal
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
    # Screen.println(str(returned_users))
    print_with_highlighted_color(query, str(returned_users))
    input("\nPress ENTER to continue...\n")


def search_content(kademlia_server):
    query = input("\nPlease enter you query: ")
    results = asyncio.run(kademlia_server.search_content(query))
    #Screen.println(str(results))
    print_with_highlighted_color(query, str(results))
    input("\nPress ENTER to continue...\n")


def search_mentions(kademlia_server):
    results = asyncio.run(kademlia_server.search_content(
        f"@{kademlia_server.username}"))

    for message, _ in results:
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

        Screen.println("Followers: " + str(data["followers"]))

        if len(data["following"]) == 0:   
            Screen.println("Following: " + str(data["following"]))
        else:
            text = ""
            text+="Following: [\'"+str(data["following"][0]["username"])+"\'"
            for i in range(1,len(data["following"])):
                text+=", "
                text+="\'"+str(data["following"][i]["username"])+"\'"
            Screen.println(text+"]")
        Screen.println("Messages: " + str(data["messages"]))

    input("\nPress ENTER to continue...\n")


def publish(kademlia_server):
    message = input("Please write the content of your message: ")
    asyncio.run(kademlia_server.publish(message, kademlia_server.username))
    input("\nPress ENTER to continue...\n")


def view_all_users(kademlia_server):
    data = asyncio.run(kademlia_server.get_info("registered_usernames"))
    kademlia_server.log_info(f"View All Users - {data}")
    Screen.println("Registered usernames:\n\n")
    Screen.println(data)
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
        "View Timeline", view_timeline, [kademlia_server])
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
        "View All Users", view_all_users, [kademlia_server])
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
    auth_menu.append_item(logout_item)

    auth_menu.show()
