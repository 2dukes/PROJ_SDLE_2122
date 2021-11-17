import pickle
import zmq
from zmq import backend
from message import Message
from proxy_backup import Backup
from os.path import exists

PROXY_FRONTEND_PORT = "6000"
PROXY_BACKEND_PORT = "6001"

FILE_PATH = "backup/proxy.backup"

class Proxy:
    def __init__(self, message_queue={}, subscriber_pointers={}):
        # Prepare our context and sockets
        context = zmq.Context()
        self.frontend = context.socket(zmq.REP)
        self.backend = context.socket(zmq.REP)
        self.frontend.bind(f"tcp://*:{PROXY_FRONTEND_PORT}")
        self.backend.bind(f"tcp://*:{PROXY_BACKEND_PORT}")

        # Initialize poll set
        self.poller = zmq.Poller()
        self.poller.register(self.frontend, zmq.POLLIN)
        self.poller.register(self.backend, zmq.POLLIN)
        
        # Initialize queue and subscriber positions
        self.message_queue = message_queue

        # { "Topic 1": {"s1": 2, "s3": 4}}
        self.subscriber_pointers = subscriber_pointers
        
    def run(self):
        # Switch messages between sockets
        while True:
            socks = dict(self.poller.poll())

            if socks.get(self.frontend) == zmq.POLLIN:
                message = Message(self.frontend.recv_multipart())
                [msg_id, topic, message] = message.decode()
                
                # Put message in shared queue
                if topic in self.message_queue:
                    self.message_queue[topic].append(message)
                else:
                    self.message_queue[topic] = [message]
                
                response_msg = Message(["ACK"], msg_id).encode()
                self.frontend.send_multipart(response_msg)

            if socks.get(self.backend) == zmq.POLLIN:
                [msg_id, msg_type, topic, subscriber_id] = Message(self.backend.recv_multipart()).decode()
                print([msg_type, topic, subscriber_id])
                
                if (msg_type == "GET"): 
                    if topic in self.subscriber_pointers:
                        response = []
                        if subscriber_id in self.subscriber_pointers[topic]:                            
                            message_index = self.subscriber_pointers[topic][subscriber_id]                         
                            if message_index >= len(self.message_queue[topic]):
                                response_msg = Message(["NO_MESSAGES_YET", "There are no pending messages yet. Please check later."])
                                response = response_msg.encode()
                            else:
                                response_msg = Message(["MESSAGE", self.message_queue[topic][message_index]])
                                response = response_msg.encode()
                                self.subscriber_pointers[topic][subscriber_id] += 1
                                lowest_index = 0 if len(self.subscriber_pointers[topic].values()) == 0 else min(self.subscriber_pointers[topic].values())
                                del self.message_queue[topic][:lowest_index]
                                for key in self.subscriber_pointers[topic].keys():
                                    self.subscriber_pointers[topic][key] -= lowest_index # Make sure this is done in place
                        else:
                            response = Message(["NOT_SUB", f"You haven't subscribed to {topic}."]).encode()
                    else:
                        response = Message(["NOT_SUB", f"You haven't subscribed to {topic}."]).encode()

                    self.backend.send_multipart(response)
                elif (msg_type == "SUB"):
                    if topic not in self.message_queue:
                        self.message_queue[topic] = []
                        
                    if topic not in self.subscriber_pointers:
                        self.subscriber_pointers[topic] = {}
                    elif (subscriber_id in self.subscriber_pointers[topic]):
                        response = Message(["SUB_ACK"]).encode()
                        self.backend.send_multipart(response)
                        continue

                    position = len(self.message_queue[topic])
                    self.subscriber_pointers[topic][subscriber_id] = position

                    response = Message(["SUB_ACK"]).encode() 
                    self.backend.send_multipart(response)
                elif (msg_type == "UNSUB"):
                    if topic in self.message_queue and topic in self.subscriber_pointers and subscriber_id in self.subscriber_pointers[topic]:
                        del self.subscriber_pointers[topic][subscriber_id]

                    response = Message(["UNSUB_ACK"]).encode() 
                    self.backend.send_multipart(response)
                else:
                    raise Exception("Invalid message type!")

if __name__ == "__main__":
    file_exists = exists(FILE_PATH)
    proxy = None
    if file_exists:
        with open(FILE_PATH, "rb") as file:
            try:
                [msg_queue, sub_pointers] = pickle.load(open(FILE_PATH, "rb"))
                #print("backup", [backup])
                proxy = Proxy(msg_queue, sub_pointers) # [message_queue, subscriber_pointers] 
                print("Message Queue:", proxy.message_queue)
                print("Subscriber pointers:", proxy.subscriber_pointers)
            except Exception as e:
                print("Catched exception!")
                print(e)
    else:
        proxy = Proxy()
    
    Backup(proxy.message_queue, proxy.subscriber_pointers).start()
    proxy.run()
    