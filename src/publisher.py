import zmq
import argparse
import yaml
import time

PROXY_IP = "127.0.0.1"
PROXY_PORT = "6000"

def read_config(publisher):
    config = yaml.safe_load(open(args.config_file))
    steps = config["steps"]

    for step in steps:
        publisher.inject(step["name"], step["number_of_times"], step["sleep_between_messages"] if "sleep_between_messages" in step else 0)
        time.sleep(step["sleep_after"] if "sleep_after" in step else 0)

class Publisher:
    def __init__(self):
        context = zmq.Context()
        self.req_socket = context.socket(zmq.REQ)
        self.req_socket.connect(f"tcp://{PROXY_IP}:{PROXY_PORT}")
        
        print(f"Connected to tcp://{PROXY_IP}:{PROXY_PORT}")
        read_config(self)

    def put(self, topic, message):
        try:
            self.req_socket.send_multipart(list(map(lambda x: x.encode("utf-8"), [topic, message])))
            response = self.req_socket.recv_multipart()
            print(response)

            if (len(response) != 1 or response[0].decode("utf-8") != "ACK"): 
                raise Exception("Error")
            else:
                print(f"Sent [{topic}] {message}")
        except (zmq.ZMQError, Exception) as err:
            print(err)
        
    def inject(self, topic, number_of_times, sleep_between_messages):
        for i in range(0, number_of_times):
            self.put(topic, f"message{i}")
            time.sleep(sleep_between_messages)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config-file', '-f', type=str, required=True, help="YAML configuration file.")
    
    args = parser.parse_args()
    
    publisher = Publisher()
    