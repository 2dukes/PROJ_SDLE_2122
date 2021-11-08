import json
import zmq
from publisher import Publisher

def put(topic, message):
    stored_data = json.load("config.json")
    rep_port = 0
    if topic in stored_data:
        pub_port = stored_data[topic]["PUB"]
        rep_port = stored_data[topic]["REP"]
    else:
        last_port_used = stored_data.values()[-1].values()[-1]
        # Each publisher will need two sockets, one for publishing(PUB) and another for receiving messages for the topics(REP)
        pub_port = last_port_used + 1
        rep_port = last_port_used + 2

        publisher = Publisher(topic, pub_port, rep_port)
        publisher.start()

        stored_data[topic] = {"PUB": pub_port, "REP": rep_port}
        with open("config.json", "w") as config_file:
            json.dump(stored_data, config_file)
    
    context = zmq.Context()
    req_socket = context.socket(zmq.REQ)
    req_socket.connect(f"tcp://localhost:{rep_port}")
    req_socket.send_string(message)


def get(topic):
    stored_data = json.load("config.json")
    pub_port = stored_data[topic]["PUB"]
    # ...

def subscribe(topic):

def unsubscribe(topic):