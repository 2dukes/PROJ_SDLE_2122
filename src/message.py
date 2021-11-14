class Message:
    def __init__(self, msg_parts):
        self.msg_parts = msg_parts

    def encode(self):
        return list(map(lambda x: x.encode("utf-8"), self.msg_parts))

    def decode(self):
        return list(map(lambda x: x.decode("utf-8"), self.msg_parts))
