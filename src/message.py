import uuid

class Message:
    def __init__(self, msg_parts, id=str(uuid.uuid4())):
        self.msg_parts = msg_parts
        self.id = id

    def encode(self):
        encoded = list(map(lambda x: x.encode("utf-8"), self.msg_parts))
        encoded.insert(0, self.id.encode("utf-8"))
        return encoded

    def decode(self):
        decoded = list(map(lambda x: x.decode("utf-8"), self.msg_parts))
        self.id = decoded[0]
        return decoded
