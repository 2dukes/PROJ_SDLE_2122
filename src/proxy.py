import pickle
import zmq
from message import Message
from proxy_backup import Backup
from os.path import exists

PROXY_FRONTEND_PORT = "6000"
PROXY_BACKEND_PORT = "6001"
MAX_TOPIC_QUEUE_SIZE = 50000

FILE_PATH = "backup/proxy"

class Proxy:
    def __init__(self, message_queue={}, subscriber_pointers={}, last_message_ids={}):
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

        # { "Topic 1": {"pub1": last_msg_id, "pub2": last_msg_id} }
        self.last_message_ids = last_message_ids
        
    def run(self):
        # Switch messages between sockets
        while True:
            socks = dict(self.poller.poll())

            if socks.get(self.frontend) == zmq.POLLIN:
                message = Message(self.frontend.recv_multipart())
                [msg_id, topic, message] = message.decode()
                print([msg_id, topic, message])

                [pub_id, seq_num] = msg_id.split("_")
                seq_num = int(seq_num)

                # Put message in shared queue
                if topic in self.message_queue and len(self.message_queue[topic]) > 0:
                    
                    # Check if duplicated message
                    if pub_id in self.last_message_ids[topic] and seq_num <= self.last_message_ids[topic][pub_id]:
                        print("Ignored: ", [msg_id, topic, message])
                    else:
                        current_len = len(self.message_queue[topic])
                        
                        # Check and enforce max queue size for each topic
                        if current_len >= MAX_TOPIC_QUEUE_SIZE: 
                            diff = current_len - MAX_TOPIC_QUEUE_SIZE
                            del self.message_queue[topic][:(diff + 1)]

                        # Store message and its id
                        self.message_queue[topic].append((msg_id, message))
                        self.last_message_ids[topic][pub_id] = seq_num
                else:
                    if topic in self.message_queue and len(self.message_queue[topic]) == 0:
                        self.message_queue[topic].append((msg_id, message))
                    else:
                        self.message_queue[topic] = [(msg_id, message)]
                    self.last_message_ids[topic] = { pub_id: seq_num }
                
                response_msg = Message(["ACK"]).encode()
                self.frontend.send_multipart(response_msg)

            if socks.get(self.backend) == zmq.POLLIN:
                [msg_id, msg_type, topic, subscriber_id] = Message(self.backend.recv_multipart()).decode()
                print([msg_id, msg_type, topic, subscriber_id])
           
                if (msg_type == "GET"): 
                    if topic in self.subscriber_pointers:
                        response = []
                        if subscriber_id in self.subscriber_pointers[topic]:                            
                            message_index = self.subscriber_pointers[topic][subscriber_id]   
                      
                            if message_index >= len(self.message_queue[topic]):
                                response_msg = Message(["NO_MESSAGES_YET", "There are no pending messages yet. Please check later."], msg_id)
                                response = response_msg.encode()
                                self.backend.send_multipart(response)
                            else:
                                response_msg = Message(["MESSAGE", self.message_queue[topic][message_index][1]], self.message_queue[topic][message_index][0])
                                response = response_msg.encode()
                                self.backend.send_multipart(response)
                                self.subscriber_pointers[topic][subscriber_id] += 1
                                lowest_index = 0 if len(self.subscriber_pointers[topic].values()) == 0 else min(self.subscriber_pointers[topic].values())
                                del self.message_queue[topic][:lowest_index] # Remove from queue old messages
                                for key in self.subscriber_pointers[topic].keys():
                                    self.subscriber_pointers[topic][key] -= lowest_index 
                        else:
                            response = Message(["NOT_SUB", f"You haven't subscribed to {topic}."], msg_id).encode()
                    else:
                        response = Message(["NOT_SUB", f"You haven't subscribed to {topic}."], msg_id).encode()

                    
                elif (msg_type == "SUB"):
                    if topic not in self.message_queue:
                        self.message_queue[topic] = []
                        
                    if topic not in self.subscriber_pointers:
                        self.subscriber_pointers[topic] = {}
                    elif (subscriber_id in self.subscriber_pointers[topic]):
                        response = Message(["SUB_ACK"], msg_id).encode()
                        self.backend.send_multipart(response)
                        continue

                    position = len(self.message_queue[topic])
                    self.subscriber_pointers[topic][subscriber_id] = position

                    response = Message(["SUB_ACK"], msg_id).encode() 
                    self.backend.send_multipart(response)

                elif (msg_type == "UNSUB"):
                    if topic in self.message_queue and topic in self.subscriber_pointers and subscriber_id in self.subscriber_pointers[topic]:
                        del self.subscriber_pointers[topic][subscriber_id]

                    response = Message(["UNSUB_ACK"], msg_id).encode() 
                    self.backend.send_multipart(response)
                else:
                    raise Exception("Invalid message type!")

if __name__ == "__main__":
    file_exists = exists(FILE_PATH)
    proxy = None
    if file_exists:
        try:
            [msg_queue, sub_pointers, last_message_ids] = pickle.load(open(FILE_PATH, "rb"))
            proxy = Proxy(msg_queue, sub_pointers, last_message_ids) 
            print("Message Queue:", proxy.message_queue)
            print("Subscriber pointers:", proxy.subscriber_pointers)
            print("Last message IDs:", proxy.last_message_ids)
        except Exception as _:
            print("An error occurred!")
    else:
        proxy = Proxy()
    
    Backup(proxy.message_queue, proxy.subscriber_pointers, proxy.last_message_ids).start()
    proxy.run()
    