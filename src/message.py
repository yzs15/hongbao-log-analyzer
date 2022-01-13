from enum import Enum
import time


class MessageType(Enum):
    Register = 0
    Name = 1
    Query = 2
    Result = 3
    Text = 4
    Task = 5
    Log = 6


class Message:
    def __init__(self, id=0, sender=0, receiver=0, typ=MessageType.Text, body=bytes([])):
        id_bytes = id.to_bytes(8, "little")
        sender_bytes = sender.to_bytes(8, "little")
        receiver_bytes = receiver.to_bytes(8, "little")
        type_bytes = typ.value.to_bytes(1, "little")
        send_time_bytes = int(time.time() * 1000000000).to_bytes(8, "little")
        self._bytes = id_bytes + sender_bytes + receiver_bytes + type_bytes + body + send_time_bytes

    @staticmethod
    def from_bytes(raw):
        msg = Message()
        msg._bytes = raw
        return msg

    def to_bytes(self):
        return self._bytes

    def id(self):
        return int.from_bytes(self._bytes[:8], "little")

    def sender(self):
        return int.from_bytes(self._bytes[8:16], "little")

    def receiver(self):
        return int.from_bytes(self._bytes[16:24], "little")

    def type(self):
        return int.from_bytes(self._bytes[24:25], "little")

    def body(self):
        return self._bytes[25:-8]

    def send_time(self):
        return int.from_bytes(self._bytes[-8:], "little")

    def __str__(self):
        return "Message[{}, {}, {}, {}, {}, {}]".format(self.id(), self.sender(), self.receiver(),
                                                        self.type(), self.body()[:5], self.send_time())
