from threading import Thread
import pickle
import time
import os

class Backup(Thread):
    def __init__(self, message_queue, subscriber_pointers):
        Thread.__init__(self)
        self.message_queue = message_queue
        self.subscriber_pointers = subscriber_pointers
        
    def run(self):
        while True:       
            # see http://stackoverflow.com/questions/7433057/is-rename-without-fsync-safe
            tmp_file = "backup/proxy_tmp.backup"  
            actual_file = "backup/proxy.backup"  
            with open(tmp_file, "wb") as file:
                pickle.dump([self.message_queue, self.subscriber_pointers], file)
                file.flush()
                os.fsync(file.fileno())

            os.rename(tmp_file, actual_file) # Atomic instruction
            time.sleep(0.01)
