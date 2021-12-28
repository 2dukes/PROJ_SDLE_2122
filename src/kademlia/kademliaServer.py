import logging
import asyncio
from kademlia.network import Server
from threading import *

class KademliaServer:
    def __init__(self, port):
        self.port = port

        self.loopThread = Thread(target=self.start_server)
        #self.timelineThread.start()
        
    def start_server(self):
        handler = logging.FileHandler('log_file.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        log = logging.getLogger('kademlia')
        log.addHandler(handler)
        log.setLevel(logging.DEBUG)

        self.loop = asyncio.get_event_loop()
        self.loop.set_debug(True)

        self.server = Server()
        self.loop.run_until_complete(self.server.listen(self.port))
        
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.server.stop()
            self.loop.close()

    def close_server(self):
        # Closes the loop after the current iteration
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.server.close()
