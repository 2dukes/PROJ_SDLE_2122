import zmq
from zmq import backend

PROXY_FRONTEND_PORT = "6000"
PROXY_BACKEND_PORT = "6001"

class Proxy:
    def __init__(self):
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
        self.message_queue = {}

        # { "Topic 1": {"s1": 2, "s3": 4}}
        self.subscriber_pointers = {}
        
    def run(self):
        # Switch messages between sockets
        while True:
            socks = dict(self.poller.poll())

            if socks.get(self.frontend) == zmq.POLLIN:
                messages = self.frontend.recv_multipart()
                [topic, message] = list(map(lambda x: x.decode("utf-8"), messages))
                
                # Put message in shared queue
                if topic in self.message_queue:
                    self.message_queue[topic].append(message)
                else:
                    self.message_queue[topic] = [message]
                    
                self.frontend.send_multipart([b"ACK"])

            if socks.get(self.backend) == zmq.POLLIN:
                messages = self.backend.recv_multipart()
                [msg_type, topic, subscriber_id] = list(map(lambda x: x.decode("utf-8"), messages))
                
                if (msg_type == "GET"):
                    if topic in self.subscriber_pointers:
                        response = []
                        if subscriber_id in self.subscriber_pointers[topic]:
                            message_index = self.subscriber_pointers[topic][subscriber_id]
                            if message_index >= len(self.message_queue[topic]):
                                response = ["NO_MESSAGES_YET".encode('utf-8'), "There are no pending messages yet. Please check later.".encode('utf-8')]
                            else:
                                response = ["MESSAGE".encode('utf-8'), self.message_queue[topic][message_index].encode("utf-8")]
                            self.subscriber_pointers[topic][subscriber_id] += 1 # make sure this is done inplace
                        else:
                            response = [f"NOT_SUB".encode("utf-8"), "You haven't subscribed to {topic}.".encode("utf-8")]
                    
                    self.backend.send_multipart(response)
                elif (msg_type == "SUB"):
                    if topic not in self.message_queue:
                        self.message_queue[topic] = []
                    if topic not in self.subscriber_pointers:
                        self.subscriber_pointers[topic] = {}
                        
                    position = len(self.message_queue[topic])
                    self.subscriber_pointers[topic][subscriber_id] = position

                    response = ["SUB_ACK".encode("utf-8")]
                    self.backend.send_multipart(response)
                elif (msg_type == "UNSUB"):
                    if topic in self.message_queue:
                        del self.subscriber_pointers[topic][subscriber_id]

                    response = ["UNSUB_ACK".encode("utf-8")]
                    self.backend.send_multipart(response)
                else:
                    raise Exception("Invalid message type!")       

if __name__ == "__main__":
    proxy = Proxy()
    proxy.run()