from typing import List
import requests
from src.message import Message, MessageType
from src.idutils import message_id
from src.zmqutils import send
from src.fileutils import save_logs
import threading
from datetime import datetime, timedelta
import os

FULL = (1 << 8) - 1
TOTAL = 256000


class Analyzer:
    def __init__(self, zmq_end, mid, sender, receiver, servers, env, last_time):
        super().__init__()
        self.zmq_end = zmq_end
        self.servers = servers
        self.mid = mid
        self.sender = sender
        self.receiver = receiver
        self.env = env
        self.last_time = last_time

        init_addr_name()
    def fake_run(self, prefix):
        print("fake_run")
        global TOTAL
        TOTAL = int(prefix.split("-")[-1])
        files = os.listdir(prefix)
        log_data = dict()
        for file in files:
            url = "http://"+file.replace("-",":").replace(".txt", "")
            if not url in self.servers:
                continue
            path = os.path.join(prefix, file)
            logs = open(path).readlines()
            add_logs(url, logs, log_data, self.last_time)
        log_data_sorted = sort_logs(log_data)

        print_logs(prefix, "log.txt", log_data_sorted)
        proof = proof_data()
        proof.timestamp = datetime.now() + timedelta(hours=8)
        if self.env == "net":
            analyze_quality_net_v2(log_data_sorted, proof, prefix)
            save_proof_csv(prefix, proof, "src/net_base.png")
            draw_proof(prefix, proof, "src/net_base.png")
        elif self.env == "spb":
            analyze_quality_spb_v2(log_data_sorted, proof, prefix)
            analyze_path(log_data_sorted, proof)
            save_proof_csv(prefix, proof, "src/spb_base.png")
            draw_proof(prefix, proof, "src/spb_base.png")
        else:
            print("UNKNOWN env:", self.env)

        proof.print_proof()
        if len(unknown_names) != 0:
            print(unknown_names)

        with open("proof.jpg", "rb") as f:
            img = f.read()
            body = FULL.to_bytes(1, "little") + img
            msg = Message(message_id(self.mid, self.sender), self.sender, self.receiver, MessageType.Text, body)
            # send(self.zmq_end, msg.to_bytes())

        return log_data_sorted[-1][1][-1].time
    def run(self):
        now = datetime.now()
        prefix = "logs/{0:04d}{1:02d}{2:02d}{3:02d}{4:02d}{5:02d}-{6}-{7:d}".format(
            now.year, now.month, now.day, now.hour, now.minute, now.second, self.env, TOTAL)
        print("Prefix: ", prefix)
        os.makedirs(prefix, exist_ok=True)

        log_data = dict()
        for server in self.servers:
            log_text = ""
            print("start request log: ", server)
            resp = requests.get(server)
            print("end request log: ", server)
            log_text += resp.text.strip() + '\n'
            save_logs(prefix, server, log_text)
            log_splits = log_text.split("\n")
            logs = []
            for sp in log_splits:
                if len(sp) == 0:
                    continue
                logs.append(sp)
            add_logs(server, logs, log_data, self.last_time)
        log_data_sorted = sort_logs(log_data)

        print_logs(prefix, "log.txt", log_data_sorted)
        proof = proof_data()
        proof.timestamp = datetime.now() + timedelta(hours=8)

        if self.env == "net":
            analyze_quality_net_v2(log_data_sorted, proof, prefix)
            save_proof_csv(prefix, proof, "src/net_base.png")
            draw_proof(prefix, proof, "src/net_base.png")
        elif self.env == "spb":
            analyze_quality_spb_v2(log_data_sorted, proof, prefix)
            analyze_path(log_data_sorted, proof)
            save_proof_csv(prefix, proof, "src/spb_base.png")
            draw_proof(prefix, proof, "src/spb_base.png")
        else:
            print("UNKNOWN env:", self.env)

        proof.print_proof()
        if len(unknown_names) != 0:
            print(unknown_names)

        with open("proof.jpg", "rb") as f:
            img = f.read()
            body = FULL.to_bytes(1, "little") + img
            msg = Message(message_id(self.mid, self.sender), self.sender, self.receiver, MessageType.Text, body)
            # send(self.zmq_end, msg.to_bytes())

        return log_data_sorted[-1][1][-1].time

    def run_local(self, dir):
        global TOTAL
        TOTAL = int(dir.split("-")[-1])
        # TOTAL = 

        log_data_sorted = load_logs_from_dir(dir, self.last_time)

        proof = proof_data()
        proof.timestamp = log_data_sorted[0][1][0].time

        # 统计保质任务情况
        # valid_logs = list_valid_logs_spb(log_data_sorted)
        # list_good_task_spb(valid_logs)

        # 获取MsgSvr发出的时间
        # bj_send_times = []
        # nj_send_times = []
        # valid_logs = list_valid_logs_spb(log_data_sorted)
        # for log_item in valid_logs:
        #     logs = log_item[1]
        #     for i in range(len(logs)):
        #         log = logs[i]
        #         if log.logger == 'BJ-MsgSevr':
        #             bj_send_times.append(logs[i+1].time)
        #             break
        #         elif log.logger == 'NJ-MsgSevr':
        #             nj_send_times.append(logs[i+1].time)
        #             break

        # with open("./nj_time.csv", "w") as f:
        #     f.write(str(nj_send_times))
        # with open("./bj_time.csv", "w") as f:
        #     f.write(str(bj_send_times))

        # 统计machine的时间
        machines = ["NJ-Machn-0", "NJ-Machn-1", "BJ-Machn-0", "BJ-Machn-1"]
        valid_logs = list_valid_logs_spb(log_data_sorted)
        time_sum = {}
        for log_item in valid_logs:
            logs = log_item[1]
            for i in range(len(logs)):
                log = logs[i]
                duration = logs[i + 2].time - logs[i + 1].time
                start_time = logs[i+1].time
                end_time = logs[i+2].time
                if log.logger in machines:
                    if log.logger not in time_sum:
                        time_sum[log.logger] = []
                    time_sum[log.logger].append("{},{},{}".format(duration, start_time, end_time))
                    break

        for machine in machines:
            with open(machine + '.csv', "w") as f:
                f.write('\n'.join(time_sum[machine]))

        # 重新计算通量
        # if self.env == "net":
        #     analyze_quality_net(log_data_sorted, proof)
            # add_proof_csv("result.csv", "net", proof)
        # elif self.env == "spb":
        #     analyze_quality_spb(log_data_sorted, proof)
        #     analyze_path(log_data_sorted, proof)
        #     add_proof_csv("result.csv", "spb", proof)

        # 分析大于50ms的原因
        # if self.env == "net":
        #     valid_logs = list_valid_logs_net(log_data_sorted)
        # elif self.env == "spb":
        #     valid_logs = list_valid_logs_spb(log_data_sorted)
        #     gt_50_logs = [log_item for log_item in valid_logs if 50000000 <= log_duration_spb(log_item)]
        #     print_logs(dir, "gt_50_logs.txt", gt_50_logs)
        #
        #     total = 0
        #     for log_item in gt_50_logs:
        #         total += log_duration_spb(log_item)
        #     print("Average duration: ", total / len(gt_50_logs))
        #
        #     gap_big = {}
        #     for log_item in gt_50_logs:
        #         logs = log_item[1]
        #         biggest_gap = 0
        #         biggest_idx = 0
        #         for i in range(len(logs)-1):
        #             if biggest_gap < logs[i+1].time - logs[i].time:
        #                 biggest_gap = logs[i+1].time - logs[i].time
        #                 biggest_idx = i
        #         if biggest_idx in gap_big:
        #             gap_big[biggest_idx] += 1
        #         else:
        #             gap_big[biggest_idx] = 1
        #     print(len(gt_50_logs), gap_big)
        # else:
        #     print("UNKNOWN env:", self.env)

        # proof.print_proof()
        if len(unknown_names) != 0:
            print(unknown_names)

        return log_data_sorted[-1][1][-1].time



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


class proof_data:
    def __init__(self):
        self.real_nums = 0
        self.timestamp = 0
        self.num_tasks = 0
        self.yield_100 = 0
        self.goodput_100 = 0
        self.yield_50 = 0
        self.goodput_50 = 0
        self.yield_20 = 0
        self.goodput_20 = 0
        self.BJ_local = 0
        self.BJ_station = 0
        self.NJ_local = 0
        self.NJ_station = 0
        self.BJ_machine1 = 0
        self.BJ_machine2 = 0
        self.NJ_machine1 = 0
        self.NJ_machine2 = 0

    def print_proof(self):
        print(self.timestamp)
        print("Number of Tasks: ", str(self.num_tasks))
        print("---------------------------------")
        print(" Exe_Time  |  Yield  |  Goodput\n")
        print("    100ms  | ", format(self.yield_100, ".2f"), "  | ", format(self.goodput_100, ".2f"))
        print("     50ms  | ", format(self.yield_50, ".2f"), "  | ", format(self.goodput_50, ".2f"))
        print("     20ms  | ", format(self.yield_20, ".2f"), "  | ", format(self.goodput_20, ".2f"))
        print("---------------------------------")
        print("     Type  | Beijing | Nanjing")
        print("    Local  | ", str(self.BJ_local).rjust(4, " "), "  |  " + str(self.NJ_local).rjust(4, " "))
        print("  Station  | ", str(self.BJ_station).rjust(4, " "), "  |  " + str(self.NJ_station).rjust(4, " "))
        print(" Machine1  | ", str(self.BJ_machine1).rjust(4, " "), "  |  " + str(self.NJ_machine1).rjust(4, " "))
        print(" Machine2  | ", str(self.BJ_machine2).rjust(4, " "), "  |  " + str(self.NJ_machine2).rjust(4, " "))
        print("---------------------------------\n")
        return


addr_name = {
    "tcp://159.226.41.229:7057": "BJ-Station",
    "tcp://10.208.104.3:7055": "BJ-LocalSw",
    "tcp://58.240.113.38:10014": "NJ-Station",
    "tcp://192.168.143.1:5560": "NJ-LocalSw",
    "tcp://159.226.41.229:8081": "BJ-MsgSevr",
    "tcp://101.43.150.136:8081": "BJ-MsgSevr",
    "tcp://58.240.113.38:10021": "NJ-MsgSevr",
    "tcp://10.208.104.3:7060": "BJ-Machn-0",
    "tcp://10.208.104.9:7062": "BJ-Machn-1",
    "tcp://192.168.143.1:5563": "NJ-Machn-0",
    "tcp://192.168.143.2:5563": "NJ-Machn-1",
    "tcp://127.0.0.1:5558": "Machn-0",
    "tcp://127.0.0.1:5560": "Machn-1",
    "0.0.1": "BJ-MsgSevr",
    "0.0.2": "NJ-MsgSevr",
    "0.1.1": "Sun       ",
    "0.1.2": "Wang      ",
    "0.2.1": "Li        ",
    "0.1048575.1048575": "Broadcast0",
    "0.1048575.2": "Broadcast1",

    "tcp://159.226.41.229:7101": "BJ-MsgSevr",
    "tcp://58.240.113.38:10018": "NJ-MsgSevr",
    "0.524288.1": "BJ-K8s    ",
    "0.524288.2": "NJ-K8s    ",
    "0.1048575.1": "BJ-MsgSevr",
}

k8s_container_names = []
unknown_names = []


def init_addr_name():
    for i in range(4, 10000):
        key_bj = "0.{}.1".format(i)
        val_bj = "ThingB{0:04d}".format(i)
        addr_name[key_bj] = val_bj

        key_nj = "0.{}.2".format(i)
        val_nj = "ThingN{0:04d}".format(i)
        addr_name[key_nj] = val_nj


def addr2name(addr, log_file):
    if addr in addr_name:
        return addr_name[addr]
    elif len(addr.split('/')) == 4:
        if addr not in k8s_container_names:
            k8s_container_names.append(addr)
        return "K8s-CT-" + str(k8s_container_names.index(addr)).zfill(3)
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
    s2 = str(time // 1000000000000).zfill(8)
    str_time = "(" + s2 + ")" + s1 + " s " + ms + " ms " + us + " us " + ns + " ns"
    # str_time = s1 + " s " + ms + " ms " + us + " us " + ns + " ns"
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


def add_logs(log_file, logs, log_data, last_time):
    for log in logs:
        items = log.split(",")
        if len(items) < 4 or int(items[3]) < last_time:
            continue

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


def load_logs_from_dir(dir, last_time):
    log_data = dict()
    filenames = os.listdir(dir)
    for filename in filenames:
        name, ext = os.path.splitext(filename)
        if name.find("log") != -1 or ext != ".txt":
            continue

        log_text = ""
        with open(os.path.join(dir, filename), "r") as f:
            log_text += f.read().strip() + '\n'
        log_splits = log_text.split("\n")

        logs = []
        for sp in log_splits:
            if len(sp) == 0:
                continue
            logs.append(sp)
        add_logs("server", logs, log_data, last_time)
    for msg_id in log_data:
        log_data[msg_id].sort(key=lambda x: x.time)
    return log_data.items()
    # return sort_logs(log_data)


def sort_logs(log_data):
    for msg_id in log_data:
        log_data[msg_id].sort(key=lambda x: x.time)
    log_list = list(log_data.items())
    log_list.sort(key=lambda x: x[1][0].time)
    return log_list


def filter_logs(log_data, filter):
    filtered = [log for log in log_data if filter(log)]
    return filtered


def print_logs(prefix, filename, log_data_sorted):
    f = open(prefix + "/" + filename, "w", encoding="utf-8")
    for logs in log_data_sorted:
        print("Message ID " + msg_id_int2dot(logs[0]) + " (" + str(logs[0]) + ")" + " #Record=" + str(len(logs[1])),
              file=f)
        for log in logs[1]:
            print(log.string(), file=f)
        print("-----------------------\n", file=f)
    f.close()


# ------------------------------------------------------------

SPB_LEN = 14
SPB_START_IDX = 2
SPB_END_IDX = SPB_LEN - 3


def log_duration_spb(log_data_item):
    logs = log_data_item[1]
    duration = logs[SPB_END_IDX].time - logs[SPB_START_IDX].time
    return duration


def list_valid_logs_spb(log_data_sorted):
    valid_logs = []
    for log_data_item in log_data_sorted:
        logs = log_data_item[1]
        if len(logs) != SPB_LEN:
            continue
        valid_logs.append(log_data_item)
    return valid_logs


def list_good_task_spb(log_data_sorted):
    under_100 = 0
    under_50 = 0
    under_20 = 0
    pos_1_100 = 0
    pos_2_100 = 0
    pos_1_all = 0
    pos_2_all = 0
    good_put_dis = {}
    for log_data_item in log_data_sorted:
        msg_id = log_data_item[0] >> 40
        dev_id = (log_data_item[0] >> 20) & ((1<<20)-1)
        pos_id = (log_data_item[0]) & ((1<<20)-1)

        logs = log_data_item[1]
        duration = logs[SPB_END_IDX].time - logs[SPB_START_IDX].time

        if duration < 100000000:
            under_100 += 1
            print(msg_id, dev_id, pos_id)
            prefix = msg_id // 100
            if prefix not in good_put_dis:
                good_put_dis[prefix] = 0
            good_put_dis[prefix] += 1
            if pos_id == 1:
                pos_1_100 += 1
            if pos_id == 2:
                pos_2_100 += 1
        if duration < 50000000:
            under_50 += 1
        if duration < 20000000:
            under_20 += 1
        if pos_id == 1:
            pos_1_all += 1
        if pos_id == 2:
            pos_2_all += 1

    for k in good_put_dis:
        print(k, good_put_dis[k])
    print(under_100, under_50, under_20)
    print("100ms", pos_1_100, pos_2_100)
    print("total", pos_1_all, pos_2_all)

def analyze_quality_spb(log_data_sorted, proof):
    total = 0
    under_100 = 0
    under_50 = 0
    under_20 = 0
    first_time = 0
    last_time = 0
    for log_data_item in log_data_sorted:
        logs = log_data_item[1]
        if len(logs) != SPB_LEN:
            continue
        total += 1
        if first_time == 0:
            first_time = logs[SPB_START_IDX].time
        elif logs[SPB_START_IDX].time < first_time:
            first_time = logs[SPB_START_IDX].time
        duration = logs[SPB_END_IDX].time - logs[SPB_START_IDX].time
        last_time = logs[SPB_END_IDX].time
        if duration < 100000000:
            under_100 += 1
        if duration < 50000000:
            under_50 += 1
        if duration < 20000000:
            under_20 += 1
    print("Number: ", total)
    proof.real_nums = total
    total = TOTAL
    proof.num_tasks = total
    proof.yield_100 = under_100 / total
    proof.yield_50 = under_50 / total
    proof.yield_20 = under_20 / total
    total_time = (last_time - first_time) * 1. / 1000000000
    proof.goodput_100 = under_100 / total_time
    proof.goodput_50 = under_50 / total_time
    proof.goodput_20 = under_20 / total_time

def analyze_quality_spb_v2(log_data_sorted, proof, prefix):
    total = 0
    under_100 = 0
    under_50 = 0
    under_20 = 0

    qos_100 = 0
    qos_50 = 0
    qos_20 = 0
    qos_good_100 = 0
    qos_good_50 = 0
    qos_good_20 = 0
    
    first_time = 0
    last_time = 0
    id_bits = ((1<<20) -1) << 40
    location_bits = (1<<20) -1
    # print(log_data_sorted)
    m20bits = 1 << 17
    m100bits = 1<<18
    task_info_detail = []
    for log_data_item in log_data_sorted:
        qos = 0
        is_good = False
        message_id = (log_data_item[0] & id_bits)>>40
        if message_id >> 19 == 1:  # 干扰消息
            continue
        if message_id <2:
            continue
        location = (log_data_item[0] & location_bits)

        logs = log_data_item[1]
        if len(logs) != SPB_LEN:
            # print(logs)
            continue
        if first_time == 0:
            first_time = logs[SPB_START_IDX].time
        total += 1
        duration = logs[SPB_END_IDX].time - logs[SPB_START_IDX].time
        last_time = logs[SPB_END_IDX].time
        if duration < 100000000:
            under_100 += 1
        if duration < 50000000:
            under_50 += 1
        if duration < 20000000:
            under_20 += 1
        if location == 1:
            if message_id % 2 == 0:
                qos=100000000
                qos_100 += 1
                if duration < 100000000:
                    qos_good_100 += 1
                    is_good=True
            if  message_id % 2 == 1:
                qos=50000000
                qos_50 += 1
                if duration < 50000000:
                    qos_good_50 += 1
                    is_good=True
        if location == 2:
            if  message_id & m20bits != 0:
                qos=20000000
                qos_20 += 1
                if duration < 20000000:
                    qos_good_20 += 1
                    is_good=True
            else:
                qos=100000000
                qos_100 += 1
                if duration < 100000000:
                    qos_good_100 += 1
                    is_good=True
        task_info_detail_add(task_info_detail, logs[NET_START_IDX].time, qos, is_good)
    task_info_detail_to_csv(task_info_detail, 1000000000, os.path.join(prefix, "task_info_detail.csv"))        
    print("Number: ", total)
    print("Qos 100: ", qos_100)
    print("Qos 50: ", qos_50)
    print("Qos 20: ", qos_20)
    print("Qos good 100: ", qos_good_100, qos_good_100/qos_100)
    print("Qos good 50: ", qos_good_50, qos_good_50/qos_50)
    print("Qos good 20: ", qos_good_20, qos_good_20/ qos_20)
    print("Qos total: ", qos_good_100+qos_good_50+qos_good_20, (qos_good_100+qos_good_50+qos_good_20) / (qos_100+qos_50+qos_20))
    print("under 100: ", under_100)
    print("under 50: ", under_50)
    print("under 20: ", under_20)

    total = TOTAL
    proof.real_nums = total
    proof.num_tasks = total
    proof.yield_100 = qos_good_100 / qos_100
    proof.yield_50 = qos_good_50 / qos_50
    proof.yield_20 = qos_good_20 / qos_20
    total_time = (last_time - first_time) * 1. / 1000000000
    proof.goodput_100 = qos_good_100 / total_time
    proof.goodput_50 = qos_good_50 / total_time
    proof.goodput_20 = qos_good_20 / total_time
  
def analyze_quality_spb_v3(log_data_sorted, proof, prefix):
    total = 0
    under_100 = 0
    under_50 = 0
    under_20 = 0

    qos_100 = 0
    qos_50 = 0
    qos_20 = 0
    qos_good_100 = 0
    qos_good_50 = 0
    qos_good_20 = 0
    
    first_time = 0
    last_time = 0
    id_bits = ((1<<20) -1) << 40
    location_bits = (1<<20) -1
    # print(log_data_sorted)
    m20bits = 1 << 17
    m100bits = 1<<18
    task_info_detail = []
    for log_data_item in log_data_sorted:
        qos = 0
        is_good = False
        message_id = (log_data_item[0] & id_bits)>>40
        if message_id >> 19 == 1:  # 干扰消息
            continue
        if message_id <2:
            continue
        location = (log_data_item[0] & location_bits)

        logs = log_data_item[1]
        if len(logs) != SPB_LEN:
            # print(logs)
            continue
        if first_time == 0:
            first_time = logs[SPB_START_IDX].time
        total += 1
        duration = logs[SPB_END_IDX].time - logs[SPB_START_IDX].time
        last_time = logs[SPB_END_IDX].time
        if duration < 100000000:
            under_100 += 1
        if duration < 50000000:
            under_50 += 1
        if duration < 20000000:
            under_20 += 1
        if location == 1:
            if message_id % 2 == 0:
                qos=100000000
                qos_100 += 1
                if duration < 100000000:
                    qos_good_100 += 1
                    is_good=True
            if  message_id % 2 == 1:
                qos=50000000
                qos_50 += 1
                if duration < 50000000:
                    qos_good_50 += 1
                    is_good=True
        if location == 2:
            if  message_id & m20bits != 0:
                qos=20000000
                qos_20 += 1
                if duration < 20000000:
                    qos_good_20 += 1
                    is_good=True
            else:
                qos=100000000
                qos_100 += 1
                if duration < 100000000:
                    qos_good_100 += 1
                    is_good=True
        task_info_detail_add(task_info_detail, logs[NET_START_IDX].time, qos, is_good)
    task_info_detail_to_csv(task_info_detail, 1000000000, os.path.join(prefix, "task_info_detail.csv"))        
    print("Number: ", total)
    print("Qos 100: ", qos_100)
    print("Qos 50: ", qos_50)
    print("Qos 20: ", qos_20)
    print("Qos good 100: ", qos_good_100, qos_good_100/qos_100)
    print("Qos good 50: ", qos_good_50, qos_good_50/qos_50)
    print("Qos good 20: ", qos_good_20, qos_good_20/ qos_20)
    print("Qos total: ", qos_good_100+qos_good_50+qos_good_20, (qos_good_100+qos_good_50+qos_good_20) / (qos_100+qos_50+qos_20))
    print("under 100: ", under_100)
    print("under 50: ", under_50)
    print("under 20: ", under_20)

    total = TOTAL
    proof.real_nums = total
    proof.num_tasks = total
    proof.yield_100 = qos_good_100 / qos_100
    proof.yield_50 = qos_good_50 / qos_50
    proof.yield_20 = qos_good_20 / qos_20
    total_time = (last_time - first_time) * 1. / 1000000000
    proof.goodput_100 = qos_good_100 / total_time
    proof.goodput_50 = qos_good_50 / total_time
    proof.goodput_20 = qos_good_20 / total_time
  

NET_LEN_1 = 8
NET_LEN_2 = 6
NET_START_IDX = 2
NET_END_IDX_1 = NET_LEN_1 - 3
NET_END_IDX_2 = NET_LEN_2 - 3


def list_valid_logs_net(log_data_sorted):
    valid_logs = []
    for log_data_item in log_data_sorted:
        msg_id = log_data_item[0] >> 40
        if msg_id >> 19 == 1:  # 干扰消息
            continue
        logs = log_data_item[1]
        if msg_id < 3:
            continue
        ll = len(logs)
        if not (ll == NET_LEN_1 or ll == NET_LEN_2) or (log_data_item[0] & (1 << 40 - 1)) == ((1 << 20) | 2):
            continue
        valid_logs.append(log_data_item)
    return valid_logs


def list_good_task_net(log_data_sorted):
    under_100 = 0
    under_50 = 0
    under_20 = 0
    pos_1_100 = 0
    pos_2_100 = 0
    pos_1_all = 0
    pos_2_all = 0
    good_put_dis = {}
    for log_data_item in log_data_sorted:
        msg_id = log_data_item[0] >> 40
        dev_id = (log_data_item[0] >> 20) & ((1<<20)-1)
        pos_id = (log_data_item[0]) & ((1<<20)-1)

        logs = log_data_item[1]
        ll = len(logs)
        if ll == NET_LEN_1:
            duration = logs[NET_END_IDX_1].time - logs[NET_START_IDX].time
        else:
            duration = logs[NET_END_IDX_2].time - logs[NET_START_IDX].time

        if duration < 100000000:
            under_100 += 1
            print(msg_id, dev_id, pos_id)
            prefix = msg_id // 100
            if prefix not in good_put_dis:
                good_put_dis[prefix] = 0
            good_put_dis[prefix] += 1
            if pos_id == 1:
                pos_1_100 += 1
            if pos_id == 2:
                pos_2_100 += 1
        if duration < 50000000:
            under_50 += 1
        if duration < 20000000:
            under_20 += 1
        if pos_id == 1:
            pos_1_all += 1
        if pos_id == 2:
            pos_2_all += 1

    for k in good_put_dis:
        print(k, good_put_dis[k])
    print(under_100, under_50, under_20)
    print("100ms", pos_1_100, pos_2_100)
    print("total", pos_1_all, pos_2_all)


# def analyze_quality_net(log_data_sorted, proof):
#     total = 0
#     under_100 = 0
#     under_50 = 0
#     under_20 = 0
#     first_time = 0
#     last_time = 0

#     valid_logs = list_valid_logs_net(log_data_sorted)
#     for log_data_item in valid_logs:
#         logs = log_data_item[1]
#         ll = len(logs)
#         if first_time == 0:
#             first_time = logs[SPB_START_IDX].time
#         elif logs[SPB_START_IDX].time < first_time:
#             first_time = logs[SPB_START_IDX].time
#         total += 1
#         if ll == NET_LEN_1:
#             duration = logs[NET_END_IDX_1].time - logs[NET_START_IDX].time
#             last_time = logs[NET_END_IDX_1].time
#         else:
#             duration = logs[NET_END_IDX_2].time - logs[NET_START_IDX].time
#             last_time = logs[NET_END_IDX_2].time
#         if duration < 100000000:
#             under_100 += 1
#         if duration < 50000000:
#             under_50 += 1
#         if duration < 20000000:
#             under_20 += 1
#     print("Number: ", total)
#     proof.real_nums = total
#     total = TOTAL
#     proof.num_tasks = total
#     proof.yield_100 = under_100 / total
#     proof.yield_50 = under_50 / total
#     proof.yield_20 = under_20 / total
#     total_time = (last_time - first_time) * 1. / 1000000000
#     proof.goodput_100 = under_100 / total_time
#     proof.goodput_50 = under_50 / total_time
#     proof.goodput_20 = under_20 / total_time

def task_info_detail_add(tasks_info_detail:List, start_time, qos, is_good):
    tasks_info_detail.append([start_time, qos, is_good])

def task_info_detail_to_csv(tasks_info_detail:List, period, path):
    tasks_info = {}
    for task in tasks_info_detail:
        time = task[0] // period
        if not tasks_info.__contains__(time):
            tasks_info[time] = [1,0]
        else:
            tasks_info[time][0] = tasks_info[time][0]+1
        if task[2]:
            tasks_info[time][1] = tasks_info[time][1]+1
        
    good_task_list = []
    for time in tasks_info:
        good_task_list.append([time, tasks_info[time][0], tasks_info[time][1]])
    
    def take_first(item):
        return item[0]
    good_task_list.sort(key=take_first)

    f = open(path, "w")
    for item in good_task_list:
        f.write("%d, %d, %d\n" % (item[0], item[1], item[2]))
    f.close()


        

def analyze_quality_net_v2(log_data_sorted, proof, prefix):
    total = 0
    under_100 = 0
    under_50 = 0
    under_20 = 0

    qos_100 = 0
    qos_50 = 0
    qos_20 = 0
    qos_good_100 = 0
    qos_good_50 = 0
    qos_good_20 = 0
    
    first_time = 0
    last_time = 0
    id_bits = ((1<<20) -1) << 40
    location_bits = (1<<20) -1

    # valid_logs = list_valid_logs_net(log_data_sorted)
    task_info_detail = []
    num_in_thing = 0
    for log_data_item in log_data_sorted:
        is_good = False
        qos = 0
        message_id = (log_data_item[0] & id_bits)>>40
        if message_id >> 19 == 1:  # 干扰消息
            continue
        if message_id <2:
            continue
        location = (log_data_item[0] & location_bits)

        logs = log_data_item[1]
        ll = len(logs)
        if ll != NET_LEN_1 and ll != NET_LEN_2:
            continue

        if ll <= NET_START_IDX:
            if ll == 1:
                num_in_thing += 1
            continue
        if first_time == 0:
            first_time = logs[NET_START_IDX].time
        elif logs[NET_START_IDX].time < first_time:
            first_time = logs[NET_START_IDX].time
        total += 1
        if ll == NET_LEN_1:
            duration = logs[NET_END_IDX_1].time - logs[NET_START_IDX].time
            last_time = logs[NET_END_IDX_1].time
        else:
            duration = logs[NET_END_IDX_2].time - logs[NET_START_IDX].time
            last_time = logs[NET_END_IDX_2].time

        
        if duration < 100000000:
            under_100 += 1
        if duration < 50000000:
            under_50 += 1
        if duration < 20000000:
            under_20 += 1
        if location == 1:
            if message_id % 2 == 0:
                qos = 100000000
                qos_100 += 1
                if duration < 100000000:
                    qos_good_100 += 1
                    is_good = True
                    
            if  message_id % 2 == 1:
                qos = 50000000
                qos_50 += 1
                if duration < 50000000:
                    qos_good_50 += 1
                    is_good = True
        if location == 2:
            if message_id % 2 == 0:
                qos = 100000000
                qos_100 += 1
                if duration < 100000000:
                    qos_good_100 += 1
                    is_good = True
            if  message_id % 4 == 1:
                qos = 50000000
                qos_50 += 1
                if duration < 50000000:
                    qos_good_50 += 1
                    is_good = True
            if  message_id % 4 == 3:
                qos = 20000000
                qos_20 += 1
                if duration < 20000000:
                    qos_good_20 += 1
                    is_good = True
        task_info_detail_add(task_info_detail, logs[NET_START_IDX].time, qos, is_good)
    task_info_detail_to_csv(task_info_detail, 1000000000, os.path.join(prefix, "task_info_detail.csv"))
    print("num_in_thing: ", num_in_thing)
    print("Number: ", total)
    print("Qos 100: ", qos_100)
    print("Qos 50: ", qos_50)
    print("Qos 20: ", qos_20)
    print("Qos good 100: ", qos_good_100, qos_good_100/qos_100)
    print("Qos good 50: ", qos_good_50, qos_good_50/qos_50)
    print("Qos good 20: ", qos_good_20, qos_good_20/ qos_20)
    print("Qos total: ", qos_good_100+qos_good_50+qos_good_20, (qos_good_100+qos_good_50+qos_good_20) / (qos_100+qos_50+qos_20))
    print("under 100: ", under_100)
    print("under 50: ", under_50)
    print("under 20: ", under_20)

    total = TOTAL
    proof.real_nums = total
    proof.num_tasks = total
    proof.yield_100 = qos_good_100 / qos_100
    proof.yield_50 = qos_good_50 / qos_50
    proof.yield_20 = qos_good_20 / qos_20
    total_time = (last_time - first_time) * 1. / 1000000000
    proof.goodput_100 = qos_good_100 / total_time
    proof.goodput_50 = qos_good_50 / total_time
    proof.goodput_20 = qos_good_20 / total_time

def analyze_quality_net_v3(log_data_sorted, proof, prefix):
    total = 0
    under_100 = 0
    under_50 = 0
    under_20 = 0

    qos_100 = 0
    qos_50 = 0
    qos_20 = 0
    qos_good_100 = 0
    qos_good_50 = 0
    qos_good_20 = 0
    
    first_time = 0
    last_time = 0
    id_bits = ((1<<20) -1) << 40
    location_bits = (1<<20) -1

    # valid_logs = list_valid_logs_net(log_data_sorted)
    m20bits = 1 << 18
    task_info_detail = []
    num_in_thing = 0
    for log_data_item in log_data_sorted:
        is_good = False
        qos = 0
        message_id = (log_data_item[0] & id_bits)>>40
        if message_id >> 19 == 1:  # 干扰消息
            continue
        if message_id <2:
            continue
        location = (log_data_item[0] & location_bits)

        logs = log_data_item[1]
        ll = len(logs)
        if ll != NET_LEN_1 and ll != NET_LEN_2:
            continue

        if ll <= NET_START_IDX:
            if ll == 1:
                num_in_thing += 1
            continue
        if first_time == 0:
            first_time = logs[NET_START_IDX].time
        elif logs[NET_START_IDX].time < first_time:
            first_time = logs[NET_START_IDX].time
        total += 1
        if ll == NET_LEN_1:
            duration = logs[NET_END_IDX_1].time - logs[NET_START_IDX].time
            last_time = logs[NET_END_IDX_1].time
        else:
            duration = logs[NET_END_IDX_2].time - logs[NET_START_IDX].time
            last_time = logs[NET_END_IDX_2].time

        
        if duration < 100000000:
            under_100 += 1
        if duration < 50000000:
            under_50 += 1
        if duration < 20000000:
            under_20 += 1
        if location == 1:
            if message_id % 2 == 0:
                qos = 100000000
                qos_100 += 1
                if duration < 100000000:
                    qos_good_100 += 1
                    is_good = True
                    
            if  message_id % 2 == 1:
                qos = 50000000
                qos_50 += 1
                if duration < 50000000:
                    qos_good_50 += 1
                    is_good = True
        if location == 2:
            if  (message_id & m20bits) != 0:
                qos=20000000
                qos_20 += 1
                if duration < 20000000:
                    qos_good_20 += 1
                    is_good=True
            else:
                qos=100000000
                qos_100 += 1
                if duration < 100000000:
                    qos_good_100 += 1
                    is_good=True
        task_info_detail_add(task_info_detail, logs[NET_START_IDX].time, qos, is_good)
    task_info_detail_to_csv(task_info_detail, 1000000000, os.path.join(prefix, "task_info_detail.csv"))
    print("num_in_thing: ", num_in_thing)
    print("Number: ", total)
    print("Qos 100: ", qos_100)
    print("Qos 50: ", qos_50)
    print("Qos 20: ", qos_20)
    print("Qos good 100: ", qos_good_100, qos_good_100/qos_100)
    print("Qos good 50: ", qos_good_50, qos_good_50/qos_50)
    print("Qos good 20: ", qos_good_20, qos_good_20/ qos_20)
    print("Qos total: ", qos_good_100+qos_good_50+qos_good_20, (qos_good_100+qos_good_50+qos_good_20) / (qos_100+qos_50+qos_20))
    print("under 100: ", under_100)
    print("under 50: ", under_50)
    print("under 20: ", under_20)

    total = TOTAL
    proof.real_nums = total
    proof.num_tasks = total
    proof.yield_100 = qos_good_100 / qos_100
    proof.yield_50 = qos_good_50 / qos_50
    proof.yield_20 = qos_good_20 / qos_20
    total_time = (last_time - first_time) * 1. / 1000000000
    proof.goodput_100 = qos_good_100 / total_time
    proof.goodput_50 = qos_good_50 / total_time
    proof.goodput_20 = qos_good_20 / total_time

def analyze_path(log_data_sorted, proof):
    for log_data_item in log_data_sorted:
        logs = log_data_item[1]

        if len(logs) != 14:
            continue

        for i in range(14):
            if logs[i].logger == "BJ-LocalSw":
                proof.BJ_local += 1
                break
            elif logs[i].logger == "NJ-LocalSw":
                proof.NJ_local += 1
                break
            else:
                continue
        for i in range(14):
            if logs[i].logger == "BJ-Station":
                proof.BJ_station += 1
                break
            elif logs[i].logger == "NJ-Station":
                proof.NJ_station += 1
                break
            else:
                continue
        for i in range(14):
            if logs[i].logger == "BJ-Machn-0":
                proof.BJ_machine1 += 1
                break
            elif logs[i].logger == "BJ-Machn-1":
                proof.BJ_machine2 += 1
                break
            elif logs[i].logger == "NJ-Machn-0":
                proof.NJ_machine1 += 1
                break
            elif logs[i].logger == "NJ-Machn-1":
                proof.NJ_machine2 += 1
                break
            else:
                continue


from PIL import Image, ImageFont, ImageDraw


def add_proof_csv(filename, env, proof):
    res_str = "{},{},{},{},{},{},{},{},{},{}\n".format(
        env, str(proof.timestamp), str(proof.num_tasks), str(proof.real_nums),
        proof.yield_100 * 100, proof.yield_50 * 100, proof.yield_20 * 100,
        proof.goodput_100, proof.goodput_50, proof.goodput_20)
    with open(filename, "a") as f:
        f.write(res_str)


def save_proof_csv(prefix, proof, base):
    env = base.replace("src/", "").replace("_base.png", "")
    res_str = "{},{},{},{},{},{},{},{},{},{}\n".format(
        env, str(proof.timestamp), str(proof.num_tasks), str(proof.real_nums),
        proof.yield_100 * 100, proof.yield_50 * 100, proof.yield_20 * 100,
        proof.goodput_100, proof.goodput_50, proof.goodput_20)
    with open("{}/result.csv".format(prefix), "w") as f:
        f.write(res_str)
    with open("{}/../result.csv".format(prefix), "a") as f:
        f.write(res_str)


def draw_proof(prefix, proof, base):
    img = Image.open(base)
    draw = ImageDraw.Draw(img)
    blue = (32, 56, 100)

    size1 = ImageFont.truetype("src/font.ttf", 65)
    draw.text((217, 236), str(proof.timestamp), blue, font=size1)
    draw.text((500, 337), str(proof.num_tasks), blue, font=size1)
    draw.text((500, 437), format(proof.yield_100 * 100, ".2f") + "%", blue, font=size1)
    draw.text((500, 538), format(proof.goodput_100, ".2f"), blue, font=size1)

    size2 = ImageFont.truetype("src/font.ttf", 50)
    draw.text((551, 1320), format(proof.yield_100 * 100, ".2f") + "%", blue, font=size2)
    draw.text((787, 1320), format(proof.yield_50 * 100, ".2f") + "%", blue, font=size2)
    draw.text((1032, 1320), format(proof.yield_20 * 100, ".2f") + "%", blue, font=size2)
    draw.text((551, 1390), format(proof.goodput_100, ".2f"), blue, font=size2)
    draw.text((787, 1390), format(proof.goodput_50, ".2f"), blue, font=size2)
    draw.text((1032, 1390), format(proof.goodput_20, ".2f"), blue, font=size2)

    size3 = ImageFont.truetype("src/font.ttf", 55)
    draw.text((364, 830), str(proof.BJ_local), blue, font=size3)
    draw.text((364, 1021), str(proof.NJ_local), blue, font=size3)
    draw.text((760, 830), str(proof.BJ_station), blue, font=size3)
    draw.text((760, 1021), str(proof.NJ_station), blue, font=size3)
    draw.text((1173, 714), str(proof.BJ_machine1), blue, font=size3)
    draw.text((1173, 855), str(proof.BJ_machine2), blue, font=size3)
    draw.text((1173, 996), str(proof.NJ_machine1), blue, font=size3)
    draw.text((1173, 1137), str(proof.NJ_machine2), blue, font=size3)

    img.save('proof.jpg')

    filename = "{}/{}.jpg".format(prefix, base.replace("src/", "").replace("_base.png", ""))
    img.save(filename)
