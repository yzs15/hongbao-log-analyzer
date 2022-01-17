import requests
from src.log import Log
from src.message import Message, MessageType
from src.idutils import message_id
from src.zmqutils import send
import threading

FULL = (1 << 8) - 1

LOG_SERVERS = [
    "http://192.168.143.3:8091/",
    "http://192.168.143.5:8091/",
    "http://192.168.143.1:8080/",
    "http://192.168.143.2:8080/",
    "http://192.168.143.3:8080/",
    "http://192.168.143.4:8080/",
    "http://192.168.143.5:8080/",
    # "http://10.208.104.9:5555/",
    # "http://58.213.121.2:10024/",
    # "http://58.213.121.2:10034/",
    # "http://58.213.121.2:10035/",
    # "http://58.213.121.2:10036/",
    # "http://58.213.121.2:10037/",
]


class Analyzer(threading.Thread):
    def __init__(self, zmq_end, mid, sender, receiver):
        super().__init__()
        self.zmq_end = zmq_end
        self.mid = mid
        self.sender = sender
        self.receiver = receiver

    def run(self):
        logs = fetch_logs()
        img = analysis_logs(logs)
        body = FULL.to_bytes(1, "little") + img
        msg = Message(message_id(self.mid, self.sender), self.sender, self.receiver, MessageType.Text, body)
        send(self.zmq_end, msg.to_bytes())


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
    with open("/hongbao-log/fake_proof.jpg", "rb") as f:
        return f.read()
