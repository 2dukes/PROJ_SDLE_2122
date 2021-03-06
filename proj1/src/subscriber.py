import zmq
import argparse
import time
import yaml
import logging
import sys
from message import Message
from utils import parseIDs, atomic_write, read_sequence_num_sub, signal_handler
import signal

PROXY_IP = "127.0.0.1"
PROXY_PORT = "6001"

BACKUP_FILE_PATH = "backup/subscribers"

MAX_RETRIES = 100
REQUEST_TIMEOUT = 3000

class Subscriber:
    def __init__(self, id):
        self.id = id
        [self.sequence_num, self.last_get_ids] = read_sequence_num_sub(f"{BACKUP_FILE_PATH}/{self.id}")
        
        self.context = zmq.Context()
        self.setup_socket()
        
        print(f"Connected to tcp://{PROXY_IP}:{PROXY_PORT}")
        self.read_config()
        

    def setup_socket(self):
        self.req_socket = self.context.socket(zmq.REQ)
        self.req_socket.connect(f"tcp://{PROXY_IP}:{PROXY_PORT}")

    def read_config(self):
        config = yaml.safe_load(open(args.config_file))
        steps = config["steps"]

        step_number = 0
        actions = []
        sleeps = []

        for step in steps:
            action = step["action"]
            
            try:
                if action == "subscribe":
                    actions.append({ "Action": "SUB", "topic": step["topic"] })
                elif action == "unsubscribe":
                    actions.append({ "Action": "UNSUB", "topic": step["topic"] })
                elif action == "get":
                    for _ in range(step["number_of_times"]):
                        actions.append({ "Action": "GET", "topic": step["topic"] })
                        sleeps.append(step["sleep_between"] if "sleep_between" in step else 0)
                        step_number += 1
                    del sleeps[-1]
                else:
                    raise Exception("Invalid action!")
            except Exception as _:
                print("An error occurred!")
            
            sleeps.append(step["sleep_after"] if "sleep_after" in step else 0)
        
        self.inject(actions[self.sequence_num:], sleeps[self.sequence_num:])
        
    def inject(self, actions, sleeps):
        for i in range(len(actions)):
            if (actions[i]["Action"] == "SUB"):
                self.subscribe(actions[i]["topic"])
            elif (actions[i]["Action"] == "UNSUB"):
                self.unsubscribe(actions[i]["topic"])
            elif (actions[i]["Action"] == "GET"):
                self.get(actions[i]["topic"])

            # Update sequence_num in publisher file.
            file_path = f"{BACKUP_FILE_PATH}/{self.id}"
            atomic_write(file_path, [self.sequence_num, self.last_get_ids])
            
            time.sleep(sleeps[i])

    def get(self, topic):
        retries_left = MAX_RETRIES
        dup_msg = False
       
        try:
            msg_id = f"{self.id}_{self.sequence_num}"
            message_parts = ["GET", topic, self.id]
            message = Message(message_parts, msg_id).encode()
            self.req_socket.send_multipart(message)
            while True:
                if (self.req_socket.poll(REQUEST_TIMEOUT) & zmq.POLLIN) != 0: 
                    msg = self.req_socket.recv_multipart()
                    [resp_msg_id, response_type, response] = Message(msg).decode()

                    possible_response_types = ["NOT_SUB", "MESSAGE", "NO_MESSAGES_YET"]
                    if response_type not in possible_response_types:
                        raise Exception("Message with invalid type received!")

                    if response_type == "MESSAGE":
                        if topic in self.last_get_ids and self.last_get_ids[topic] == resp_msg_id:
                            print("Ignored response: ", [resp_msg_id, response_type, response])
                            print("Retrying GET...")
                            time.sleep(3) # Delay send()
                            dup_msg = True
                        else:
                            dup_msg = False
                            self.last_get_ids[topic] = resp_msg_id
                    else:
                        dup_msg = False

                    if not dup_msg:
                        self.sequence_num += 1
                        print(f"Response: {response}")
                        return 

                retries_left -= 1
                

                if retries_left == 0:
                    if dup_msg:
                        self.sequence_num += 1
                        print("Proxy can't seem to given a message other than duplicated.")
                        return
                    else:
                        print("Proxy seems to be offline, abandoning...")
                        self.req_socket.setsockopt(zmq.LINGER, 0)
                        self.req_socket.close()
                        sys.exit()
                
                # Socket is confused. Close and remove it.
                self.req_socket.setsockopt(zmq.LINGER, 0)
                self.req_socket.close()
                
                self.req_socket = self.context.socket(zmq.REQ)
                self.req_socket.connect(f"tcp://{PROXY_IP}:{PROXY_PORT}")
                
                if not dup_msg:
                    print("Reconnecting to Proxy???")
                    print(f"Resending {message}")

                self.req_socket.send_multipart(message)
        except (zmq.ZMQError, Exception) as _:
            print("An error occurred!")
    
    def sub_unsub(self, prefix, topic):
        retries_left = MAX_RETRIES
        
        try:
            msg_id = f"{self.id}_{self.sequence_num}"
            message_parts = [prefix, topic, self.id]
            message = Message(message_parts, msg_id).encode()
            self.req_socket.send_multipart(message)
            while True:
                if (self.req_socket.poll(REQUEST_TIMEOUT) & zmq.POLLIN) != 0:
                    [_, response] = Message(self.req_socket.recv_multipart()).decode()

                    self.sequence_num += 1
                    
                    
                    if response != f"{prefix}_ACK":
                        raise Exception(f"{prefix} message was not received!")
                    else:
                        action = "Subscribed to" if prefix == "SUB" else "Unsubscribed from"
                        print(f"{action} topic: [{topic}]")
                    
                        return

                retries_left -= 1
                logging.warning("No response from Proxy.")

                self.req_socket.setsockopt(zmq.LINGER, 0)
                self.req_socket.close()
                
                if retries_left == 0:
                    sys.exit()
                
                print("Reconnecting to Proxy???")

                self.req_socket = self.context.socket(zmq.REQ)
                self.req_socket.connect(f"tcp://{PROXY_IP}:{PROXY_PORT}")
                print(f"Resending {message}")
                self.req_socket.send_multipart(message)
        except (zmq.ZMQError, Exception) as _:
            print("An error occurred!")

    def subscribe(self, topic):
        self.sub_unsub("SUB", topic)
                
    def unsubscribe(self, topic):
        self.sub_unsub("UNSUB", topic)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-file", "-f", type=str, required=True, help="YAML configuration file.")
    parser.add_argument("--id", "-i", type=parseIDs, required=True, help="Subscriber ID.")

    args = parser.parse_args()
    subscriber = Subscriber(args.id)
