from threading import Thread
import pickle
import time
import os
from utils import atomic_write
import signal
from utils import signal_handler

class Backup(Thread):
    def __init__(self, message_queue, subscriber_pointers, last_message_ids):
        signal.signal(signal.SIGINT, signal_handler)
        Thread.__init__(self)
        self.message_queue = message_queue
        self.subscriber_pointers = subscriber_pointers
        self.last_message_ids = last_message_ids
        
    def run(self):
        while True:       
            atomic_write("backup/proxy", [self.message_queue, self.subscriber_pointers, self.last_message_ids])
            time.sleep(0.01)
