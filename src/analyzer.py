import requests
from src.message import Message, MessageType
from src.idutils import message_id
from src.zmqutils import send
import threading

FULL = (1 << 8) - 1


class Analyzer(threading.Thread):
    def __init__(self, zmq_end, mid, sender, receiver, servers, env):
        super().__init__()
        self.zmq_end = zmq_end
        self.servers = servers
        self.mid = mid
        self.sender = sender
        self.receiver = receiver
        self.env = env

    def run(self):
        log_data = dict()
        for server in self.servers:
            log_text = ""
            resp = requests.get(server)
            log_text += resp.text.strip() + '\n'
            log_splits = log_text.split("\n")
            logs = []
            for sp in log_splits:
                if len(sp) == 0:
                    continue
                logs.append(sp)
            add_logs(server, logs, log_data)
        sort_logs(log_data)
        img = analyze_logs(log_data)
        body = FULL.to_bytes(1, "little") + img
        msg = Message(message_id(self.mid, self.sender), self.sender, self.receiver, MessageType.Text, body)
        send(self.zmq_end, msg.to_bytes())


class event_log:
    def __init__(self):
        self.time = 0
        self.logger = ""
        self.send = ""
        self.recv = ""
        self.event = ""

    def string(self):
        time = print_time(self.time)
        if self.event == "send":
            log = "[" + time + "] ┌" + self.event.upper() + " " + self.logger
        else:
            log = "[" + time + "] └" + self.event.upper() + " " + self.logger
        log_with_send_recv = log + "  (" + self.send + " -> " + self.recv + ")"
        return log_with_send_recv


addr_name = {
    "tcp://192.168.143.1:5555": "BJ-Station",
    "tcp://192.168.143.3:5555": "BJ-LocalSw",
    "tcp://192.168.143.4:5555": "NJ-Station",
    "tcp://192.168.143.5:5555": "NJ-LocalSw",
    "tcp://192.168.143.3:8081": "BJ-MsgSevr",
    "tcp://192.168.143.5:8081": "NJ-MsgSevr",
    "tcp://127.0.0.1:5558": "Machn-0",
    "tcp://127.0.0.1:5560": "Machn-1",
    "0.0.1": "BJ-MsgSevr",
    "0.0.2": "NJ-MsgSevr",
    "0.1.1": "Wang      ",
    "0.1.2": "Sun       ",
    "0.2.1": "Li        ",
    "0.2.2": "Things-N22",
    "0.3.1": "Things-B31",
    "0.3.2": "Things-N32",
    "0.4.1": "Things-B41",
    "0.4.2": "Things-N42",
    "0.5.1": "Things-B51",
    "0.5.2": "Things-N52",
    "0.6.1": "Things-B61",
    "0.6.2": "Things-N62",
    "0.7.1": "Things-B71",
    "0.7.2": "Things-N72",
    "0.8.1": "Things-B81",
    "0.8.2": "Things-N82",
    "0.1048575.1048575": "Broadcast0",
    "0.1048575.2": "Broadcast1",
}
local_name = {
    "http://192.168.143.1:8080": "BJ-",
    "http://192.168.143.2:8080": "BJ-",
    "http://192.168.143.3:8080": "BJ-",
    "http://192.168.143.4:8080": "NJ-",
    "http://192.168.143.5:8080": "NJ-",
}
unknown_names = []


def addr2name(addr, log_file):
    if addr in addr_name:
        if addr_name[addr][0:5] == "Machn":
            return local_name[log_file] + addr_name[addr]
        else:
            return addr_name[addr]
    else:
        if addr not in unknown_names:
            unknown_names.append(addr)
        return addr


def msg_id_dot2int(dot_msg_id):
    nums = dot_msg_id.split(".")
    a = int(nums[0])
    b = int(nums[1])
    c = int(nums[2])
    return (a << 40) | (b << 20) | c


def msg_id_int2dot(int_msg_id):
    a = str(int_msg_id >> 40)
    b = str((int_msg_id >> 20) & ((1 << 20) - 1))
    c = str(int_msg_id & ((1 << 20) - 1))
    return a + "." + b + "." + c


def print_time(time):
    ns = str(time % 1000).zfill(3)
    us = str((time % 1000000) // 1000).zfill(3)
    ms = str((time % 1000000000) // 1000000).zfill(3)
    s1 = str((time % 1000000000000) // 1000000000).zfill(3)
    # s2 = str(time // 1000000000000).zfill(8)
    # str_time = "("+s2+")"+s1+" s "+ms+" ms "+us+" us "+ns+" ns"
    str_time = s1 + " s " + ms + " ms " + us + " us " + ns + " ns"
    return str_time


def fetch_logs(filename):
    logs = []
    with open(filename, "r") as f:
        for line in f.readlines():
            if len(line) < 5:
                continue
            line = line.strip()
            logs.append(line)
    return logs


def add_logs(log_file, logs, log_data):
    for log in logs:
        items = log.split(",")
        log_item = event_log()
        log_item.send = addr2name(items[0], log_file)
        log_item.recv = addr2name(items[1], log_file)
        log_item.logger = addr2name(items[2], log_file)
        log_item.time = int(items[3])
        if '.' in items[4]:
            msg_id = msg_id_dot2int(items[4])
        else:
            msg_id = int(items[4])
        log_item.event = items[5]
        if msg_id in log_data:
            log_data[msg_id].append(log_item)
        else:
            log_data[msg_id] = [log_item]


def sort_logs(log_data):
    for msg_id in log_data:
        log_data[msg_id].sort(key=lambda x: x.time)


def print_logs(log_data):
    f = open("log.txt", "w", encoding="utf-8")
    for msg_id in log_data:
        print("Message ID " + msg_id_int2dot(msg_id) + " (" + str(msg_id) + ")", file=f)
        for log in log_data[msg_id]:
            print(log.string(), file=f)
        print("-----------------------\n", file=f)
    f.close()


# ------------------------------------------------------------

def analyze_quality(log_data):
    total = 0
    good = 0
    for msg_id in log_data:
        logs = log_data[msg_id]
        if len(logs) != 10 and len(logs) != 8:
            continue
        total += 1
        time1 = logs[13].time - logs[0].time
        if time1 < 100000000:
            good += 1
    return total, good / total


def analyze_path(log_data):
    path = [[0 for col in range(4)] for row in range(2)]
    for msg_id in log_data:
        logs = log_data[msg_id]
        if len(logs) != 14:
            continue
        if logs[5].logger == "BJ-Station":
            station = 0
        elif logs[5].logger == "NJ-Station":
            station = 1
        else:
            print("Can not recognize message ", msg_id)
            continue

        if logs[7].logger == "BJ-Machn-0":
            machine = 0
        elif logs[7].logger == "BJ-Machn-1":
            machine = 1
        elif logs[7].logger == "NJ-Machn-0":
            machine = 2
        elif logs[7].logger == "NJ-Machn-1":
            machine = 3
        else:
            print("Can not recognize message ", msg_id)
            continue

        path[station][machine] += 1
    return path


from PIL import Image, ImageFont, ImageDraw


def analyze_logs(log_data):
    img = Image.open("src/base.jpg")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("src/OpenSans-Bold.ttf", 100)

    from datetime import datetime
    now = datetime.now()
    draw.text((150, 330), str(now), (0, 0, 0), font=font)

    total, quality = analyze_quality(log_data)
    draw.text((670, 2173), str(total), (0, 0, 0), font=font)
    draw.text((1380, 2173), str(quality), (0, 0, 0), font=font)

    path = analyze_path(log_data)
    draw.text((300, 920), str(sum(path[0])), (0, 0, 0), font=font)
    draw.text((1200, 920), str(sum(path[0])), (0, 0, 0), font=font)
    draw.text((300, 1870), str(sum(path[1])), (0, 0, 0), font=font)
    draw.text((1200, 1870), str(sum(path[1])), (0, 0, 0), font=font)
    draw.text((2150, 710), str(path[0][0] + path[1][0]), (0, 0, 0), font=font)
    draw.text((2150, 1160), str(path[0][1] + path[1][1]), (0, 0, 0), font=font)
    draw.text((2150, 1660), str(path[0][2] + path[1][2]), (0, 0, 0), font=font)
    draw.text((2150, 2120), str(path[0][3] + path[1][3]), (0, 0, 0), font=font)

    img.save('proof.jpg')
    with open("proof.jpg", "rb") as f:
        return f.read()
