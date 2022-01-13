import requests
from src.log import Log
from src.message import Message, MessageType
from src.idutils import message_id
from src.zmqutils import send
import threading

FULL = (1 << 8) - 1

LOG_SERVERS = [
    "http://10.208.104.9:5552/",
    "http://58.213.121.2:10024/"
]

ZMQ_ENDPOINT = "tcp://10.208.104.9:5557"


class Analyzer(threading.Thread):
    def __init__(self, mid, sender, receiver):
        super().__init__()
        self.mid = mid
        self.sender = sender
        self.receiver = receiver

    def run(self):
        logs = fetch_logs()
        img = analysis_logs(logs)
        body = FULL.to_bytes(1, "little") + img
        msg = Message(message_id(self.mid, self.sender), self.sender, self.receiver, MessageType.Text, body)
        send(ZMQ_ENDPOINT, msg.to_bytes())


def fetch_logs():
    log_text = ""
    for server in LOG_SERVERS:
        resp = requests.get(server)
        log_text += resp.text.strip() + '\n'
    log_splits = log_text.split("\n")

    logs = []
    for sp in log_splits:
        if len(sp) == 0:
            continue
        logs.append(Log(sp))
    return logs


def analysis_logs(logs):
    with open("fake_proof.jpg", "rb") as f:
        return f.read()
