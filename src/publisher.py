import zmq
import argparse
import yaml
import time
import sys
import logging
from os.path import exists
from os import rename
from message import Message
from utils import parseIDs, atomic_write, read_sequence_num_pub
import pickle

PROXY_IP = "127.0.0.1"
PROXY_PORT = "6000"

BACKUP_FILE_PATH = "backup/publishers"

MAX_RETRIES = 100
REQUEST_TIMEOUT = 3000

class Publisher:
    def __init__(self):
        self.id = args.id
        self.sequence_num = read_sequence_num_pub(f"{BACKUP_FILE_PATH}/{self.id}")
        
        self.context = zmq.Context()
        self.setup_socket()
        
        print(f"Connected to tcp://{PROXY_IP}:{PROXY_PORT}")
        self.read_config()

    def read_config(self):
        config = yaml.safe_load(open(args.config_file))
        steps = config["steps"]
        step_number = 0

        put_steps = []
        sleep_steps = []

        for step in steps:            
            for i in range(int(step["number_of_times"])):
                msg = step["message"]
                put_steps.append({ "topic" : step["topic"], "message": f"{msg}_{step_number}"})
                sleep_steps.append(step["sleep_between_messages"] if "sleep_between_messages" in step else 0)
                step_number += 1
            
            del sleep_steps[-1]
            sleep_steps.append(step["sleep_after"] if "sleep_after" in step else 0)

        self.inject(put_steps[self.sequence_num:], sleep_steps[self.sequence_num:])

    def setup_socket(self):
        self.req_socket = self.context.socket(zmq.REQ)
        self.req_socket.connect(f"tcp://{PROXY_IP}:{PROXY_PORT}")

    def put(self, topic, message):
        retries_left = MAX_RETRIES

        try:
            msg_id = f"{self.id}_{self.sequence_num}"
            sendMessage = Message([topic, message], msg_id).encode()
            self.req_socket.send_multipart(sendMessage)
            while True:
                if (self.req_socket.poll(REQUEST_TIMEOUT) & zmq.POLLIN) != 0:
                    recvMessage = Message(self.req_socket.recv_multipart())
                    
                    [_, response_type] = recvMessage.decode()
                    
                    self.sequence_num += 1

                    if response_type != "ACK":
                        raise Exception("Put request was not received!")
                    else:
                        print(f"Sent [{topic}] {message}") 
                        return
                
                retries_left -= 1
                logging.warning("No response from Proxy.")
                # Socket is confused. Close and remove it.
                self.req_socket.setsockopt(zmq.LINGER, 0)
                self.req_socket.close()

                if retries_left == 0:
                    print("Proxy seems to be offline, abandoning")
                    sys.exit()
                
                print("Reconnecting to Proxy…")

                self.req_socket = self.context.socket(zmq.REQ)
                self.req_socket.connect(f"tcp://{PROXY_IP}:{PROXY_PORT}")
                print("Resending (%s)", sendMessage)
                self.req_socket.send_multipart(sendMessage)
        except (zmq.ZMQError, Exception) as err:
            print(err)
        
    def inject(self, puts, sleeps):
        for i in range(len(puts)):
            self.put(puts[i]["topic"], puts[i]["message"])

            # Update sequence_num in publisher file.
            file_path = f"{BACKUP_FILE_PATH}/{self.id}"
            atomic_write(file_path, self.sequence_num)

            time.sleep(sleeps[i])
            

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config-file', '-f', type=str, required=True, help="YAML configuration file.")
    parser.add_argument("--id", "-i", type=parseIDs, required=True, help="Publisher ID.")
    
    args = parser.parse_args()
    
    publisher = Publisher()
    