import zmq
import argparse
import yaml
import time
import traceback
from message import Message

PROXY_IP = "127.0.0.1"
PROXY_PORT = "6000"


class Publisher:
    def __init__(self):
        self.context = zmq.Context()
        self.setup_socket()
        
        print(f"Connected to tcp://{PROXY_IP}:{PROXY_PORT}")
        self.read_config()

    def read_config(self):
        config = yaml.safe_load(open(args.config_file))
        steps = config["steps"]

        for step in steps:
            self.inject(step["topic"], step["message"], step["number_of_times"], step["sleep_between_messages"] if "sleep_between_messages" in step else 0)
            time.sleep(step["sleep_after"] if "sleep_after" in step else 0)

    def setup_socket(self):
        self.req_socket = self.context.socket(zmq.REQ)
        self.req_socket.setsockopt(zmq.RCVTIMEO, 3000) # milliseconds
        self.req_socket.connect(f"tcp://{PROXY_IP}:{PROXY_PORT}")

    def wait_for_proxy(self, topic, message):
        while True:
            self.setup_socket()
            if self.put(topic, message, True):
                return

    def put(self, topic, message, is_polling=False):
        try:
            sendMessage = Message([topic, message]).encode()
            self.req_socket.send_multipart(sendMessage)

            recvMessage = Message(self.req_socket.recv_multipart())
            [_, response_type] = recvMessage.decode()

            #if (len(response) != 2 or response_type != "ACK"): 
            if response_type != "ACK":
                raise Exception("Error")
            else:
                print(f"Sent [{topic}] {message}")
                
            return True
        except (zmq.ZMQError, Exception) as err:
            print(err)
            if not is_polling:
                print("Proxy went down. Waiting for its recovery...")
                self.wait_for_proxy(topic, message)
            return False
        
    def inject(self, topic, message_prefix, number_of_times, sleep_between_messages):
        for i in range(0, number_of_times):
            self.put(topic, f"{message_prefix}_{i}")
            time.sleep(sleep_between_messages)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config-file', '-f', type=str, required=True, help="YAML configuration file.")
    
    args = parser.parse_args()
    
    publisher = Publisher()
    