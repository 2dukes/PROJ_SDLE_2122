import zmq
import argparse
import time
import yaml
from message import Message

PROXY_IP = "127.0.0.1"
PROXY_PORT = "6001"

class Subscriber:
    def __init__(self, id):
        context = zmq.Context()

        self.req_socket = context.socket(zmq.REQ)
        self.req_socket.connect(f"tcp://{PROXY_IP}:{PROXY_PORT}")
        self.id = id
        
        print(f"Connected to tcp://{PROXY_IP}:{PROXY_PORT}")
        self.read_config()

    def read_config(self):
        config = yaml.safe_load(open(args.config_file))
        steps = config["steps"]

        for step in steps:
            action = step["action"]
            try:
                if action == "subscribe":
                    self.subscribe(step["topic"])
                elif action == "unsubscribe":
                    self.unsubscribe(step["topic"])
                elif action == "get":
                    self.inject(step["topic"], step["number_of_times"], step["sleep_between"] if "sleep_between" in step else 0)
                else:
                    raise Exception("Invalid action!")
            except Exception as err:
                print(err)
            time.sleep(step["sleep_after"] if "sleep_after" in step else 0)
        
    def inject(self, topic, number_of_times, sleep_between):
        for _ in range(0, number_of_times):
            self.get(topic)
            time.sleep(sleep_between)

    def poll_get(self, topic):
        while True:
            if self.get(topic, True):
                return
            time.sleep(1)
    
    def get(self, topic, is_polling=False):
        message_parts = ["GET", topic, self.id]
        message = Message(message_parts).encode()
        self.req_socket.send_multipart(message)
        [response_type, response] = Message(self.req_socket.recv_multipart()).decode()

        print(f"Response: {response}")
        
        possible_response_types = ["NOT_SUB", "MESSAGE", "NO_MESSAGES_YET"]
        print(response_type)
        if response_type in possible_response_types:
            if response_type == "NO_MESSAGES_YET" and not is_polling:
                self.poll_get(topic)
            if response_type == "NO_MESSAGES_YET" and is_polling:
                return False
        else:
            print("Message with invalid type received!")
    
        return True
    
    def sub_unsub(self, prefix, topic):
        try:
            message_parts = [prefix, topic, self.id]
            message = Message(message_parts).encode()
            self.req_socket.send_multipart(message)

            [response] = Message(self.req_socket.recv_multipart()).decode()
             
            if response != f"{prefix}_ACK":
                raise Exception("Error")
            else:
                action = "Subscribed" if prefix == "SUB" else "Unsubscribed"
                print(f"{action} to topic: [{topic}]")
             
            
        except (zmq.ZMQError, Exception) as err:
            print(err)

    def subscribe(self, topic):
        self.sub_unsub("SUB", topic)
                
    def unsubscribe(self, topic):
        self.sub_unsub("UNSUB", topic)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-file", "-f", type=str, required=True, help="YAML configuration file.")
    parser.add_argument("--id", "-i", type=str, required=True, help="Subscriber ID.")

    args = parser.parse_args()
    subscriber = Subscriber(args.id)
