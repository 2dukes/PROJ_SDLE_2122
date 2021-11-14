from threading import Thread
import pickle
import time

class Backup(Thread):
    def __init__(self, message_queue, subscriber_pointers):
        Thread.__init__(self)
        self.message_queue = message_queue
        self.subscriber_pointers = subscriber_pointers
        
    def run(self):
        while True:
            with open("backup/proxy.backup", "wb") as file:
                pickle.dump([self.message_queue, self.subscriber_pointers], file)
            
            time.sleep(5)
