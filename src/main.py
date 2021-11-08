import sys
import time
import zmq
import toml

from operations import put
from operations import get
from operations import subscribe
from operations import unsubscribe

operation = sys.argv[1]
topic = sys.argv[2]

if operation == "put":
    message = sys.argv[3]
    put(topic, message)
elif operation == "get":
    get(topic)
elif operation == "subscribe":
    subscribe(topic)
elif operation == "unsubscribe":
    unsubscribe(topic)
else:
    print("Invalid arguments provided!")