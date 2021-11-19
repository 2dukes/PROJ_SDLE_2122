import zmq
import argparse
import yaml
import time
import sys
import logging
from message import Message

PROXY_IP = "127.0.0.1"
PROXY_PORT = "6000"

MAX_RETRIES = 3
REQUEST_TIMEOUT = 3000

class Publisher:
    def __init__(self):
        self.context = zmq.Context()
        self.setup_socket()
        
        logging.info(f"Connected to tcp://{PROXY_IP}:{PROXY_PORT}")
        self.read_config()

    def read_config(self):
        config = yaml.safe_load(open(args.config_file))
        steps = config["steps"]

        for step in steps:
            self.inject(step["topic"], step["message"], step["number_of_times"], step["sleep_between_messages"] if "sleep_between_messages" in step else 0)
            time.sleep(step["sleep_after"] if "sleep_after" in step else 0)

    def setup_socket(self):
        self.req_socket = self.context.socket(zmq.REQ)
        self.req_socket.connect(f"tcp://{PROXY_IP}:{PROXY_PORT}")

    def put(self, topic, message):
        retries_left = MAX_RETRIES

        try: 
            sendMessage = Message([topic, message]).encode()
            self.req_socket.send_multipart(sendMessage)
            while True:
                if (self.req_socket.poll(REQUEST_TIMEOUT) & zmq.POLLIN) != 0:
                    recvMessage = Message(self.req_socket.recv_multipart())
                    [_, response_type] = recvMessage.decode()

                    if response_type != "ACK":
                        raise Exception("Put request was not received!")
                    else:
                        logging.info(f"Sent [{topic}] {message}")
                        return
                
                retries_left -= 1
                logging.warning("No response from Proxy.")
                # Socket is confused. Close and remove it.
                self.req_socket.setsockopt(zmq.LINGER, 0)
                self.req_socket.close()

                if retries_left == 0:
                    logging.error("Server seems to be offline, abandoning")
                    sys.exit()
                
                logging.info("Reconnecting to Proxy…")

                self.req_socket = self.context.socket(zmq.REQ)
                self.req_socket.connect(f"tcp://{PROXY_IP}:{PROXY_PORT}")
                logging.info("Resending (%s)", sendMessage)
                self.req_socket.send_multipart(sendMessage)
        except (zmq.ZMQError, Exception) as err:
            print(err)
            # logging.error(err)
        
    def inject(self, topic, message_prefix, number_of_times, sleep_between_messages):
        for i in range(0, number_of_times):
            self.put(topic, f"{message_prefix}_{i}")
            time.sleep(sleep_between_messages)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config-file', '-f', type=str, required=True, help="YAML configuration file.")
    
    args = parser.parse_args()
    
    publisher = Publisher()
    