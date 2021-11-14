import zmq
import argparse
import uuid
import time

PROXY_IP = "127.0.0.1"
PROXY_PORT = "6001"

class Subscriber:
    def __init__(self):
        context = zmq.Context()

        self.req_socket = context.socket(zmq.REQ)
        self.req_socket.connect(f"tcp://{PROXY_IP}:{PROXY_PORT}")
        self.id = str(uuid.uuid4())

        print(f"Connected to tcp://{PROXY_IP}:{PROXY_PORT}")
        
    def poll_get(self, topic):
        # poller = zmq.Poller()
        # poller.register(self.req_socket, zmq.POLLIN)
        
        # while True:
        #     socks = dict(poller.poll())
            
        #     if socks.get(self.req_socket) == zmq.POLLIN:
        #        message = self.req_socket.recv_multipart()
        while True:
            if self.get(topic, True):
                return
            time.sleep(1)
    
    def get(self, topic, is_polling=False):
        message_parts = ["GET", topic, self.id]
        message = list(map(lambda x: x.encode("utf-8"), message_parts))
        print(message)
        self.req_socket.send_multipart(message)
        print("After Send...")
        [response_type, response] = list(map(lambda x: x.decode("utf-8"), self.req_socket.recv_multipart()))

        print(f"Response: {response}")
        
        possible_response_types = ["NOT_SUB", "MESSAGE", "NO_MESSAGES_YET"]
        
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
            message = list(map(lambda x: x.encode("utf-8"), message_parts))
            self.req_socket.send_multipart(message)

            [response] = map(lambda x: x.decode("utf-8"), self.req_socket.recv_multipart())

          
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

    args = parser.parse_args()
    subscriber = Subscriber()

    subscriber.subscribe("topic1")
    time.sleep(3)
    subscriber.get("topic1")

