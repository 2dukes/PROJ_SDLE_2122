import zmq
from threading import Thread

class Publisher(Thread):
    def __init__(self, topic, pub_port, rep_port):
        Thread.__init__(self)
        
        self.topic = topic
        self.pub_port = pub_port
        self.rep_port = rep_port

    def run(self):
        context = zmq.Context()

        rep_socket = context.socket(zmq.REP)
        rep_socket.bind(f"tcp://*:{self.rep_port}")

        pub_socket = context.socket(zmq.PUB)
        pub_socket.bind(f"tcp://*{self.pub_port}")

        while True:
            new_message = rep_socket.recv_string()
            pub_socket.send_string(f"{self.topic} {new_message}")