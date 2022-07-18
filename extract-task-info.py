import os
import re
import sys
from calculate_need import check_noise, check_warm, get_location, check_person, get_qos
from src.analyzer_local import load_logs_from_dir, msg_id_dot2int, msg_id_int2dot
from multiprocessing import Pool, Lock, Queue, Process, Manager
from calculate_need_usage_alloc import load_comp_ranges, get_mac_parent
import json
import hashlib


def next_msg(que, parent):
    if skip(parent):
        return None
    
    log_dirpath = None
    for file in os.listdir(parent):
        if not os.path.isdir(os.path.join(parent, file)):
            continue
        if file.startswith('2022'):
            log_dirpath = os.path.join(parent, file)
            break
    log_fd = open(os.path.join(log_dirpath, 'log.txt'), 'r')
    
    message_id = 0
    logs = []
    while True:
        line = log_fd.readline()
        if line == '':
            break
        
        line = line.strip()
        if line == '':
            continue
        if '----' in line:
            assert len(logs) <= 14, 'log length greater than 14'
            que.put([message_id, logs])
            message_id = 0
            logs = []
        
        if 'Message ID' in line:
            message_id = int(re.search('\(([0-9]+)\)', line).group(1))
        elif 'SEND' in line or 'RECV' in line:
            assert message_id > 0
            ts_matchs = re.search(r'\[\((\d+)\)(\d+) s (\d+) ms (\d+) us (\d+) ns\]', line)
            ts_pre = int(ts_matchs.group(1))
            ts_sec = int(ts_matchs.group(2))
            ts_ms = int(ts_matchs.group(3))
            ts_us = int(ts_matchs.group(4))
            ts_ns = int(ts_matchs.group(5))
            ts = ts_ns + ts_us * 1000 + ts_ms * 1000000 + ts_sec * 1000000000 \
                 + ts_pre * 1000000000000
            logs.append(ts)
    que.put([0, []])
    return 0


def skip(parent):
    mac_parent = get_mac_parent(parent)
    suffix = hashlib.md5(mac_parent.encode('utf-8')).hexdigest()[:6]
    task_info_path = os.path.join(parent, f'task-info-{suffix}.csv')
    if os.path.exists(task_info_path) and os.path.getsize(task_info_path) > 0:
        return True
    return False

SPB_LEN = 14
SPB_START_IDX = 2
SPB_END_IDX = SPB_LEN - 3

NET_LEN_1 = 8
NET_LEN_2 = 6
NET_START_IDX = 2
NET_END_IDX_1 = NET_LEN_1 - 3
NET_END_IDX_2 = NET_LEN_2 - 3

def extract(que, parent):
    if skip(parent):
        return None
    print(os.getpid(), '====> extract_task_info', parent)
    
    env = 'net' if 'net' in parent else 'spb'
    record_total = ""
    while True:
        msg_id, logs = que.get()
        if msg_id == 0:
            break
        if check_noise(msg_id) or check_warm(msg_id) or check_person(msg_id):
            continue
        
        log_len = len(logs)
        id_str = msg_id_int2dot(msg_id)
        qos = get_qos(msg_id)
        duration = -1
        if env == 'net':
            if log_len == NET_LEN_1:
                duration = logs[NET_END_IDX_1] - logs[NET_START_IDX]
            elif log_len == NET_LEN_2:
                duration = logs[NET_END_IDX_2] - logs[NET_START_IDX] 
        else:
            if log_len == SPB_LEN:
                duration = logs[SPB_END_IDX] - logs[SPB_START_IDX]
        is_good = False if duration == -1 or duration > qos else True

        record = ','.join(map(str, [msg_id, id_str, qos, duration, is_good]))
        record_total += record + '\n'
    
    mac_parent = get_mac_parent(parent)
    suffix = hashlib.md5(mac_parent.encode('utf-8')).hexdigest()[:6]
    task_info_path = os.path.join(parent, f'task-info-{suffix}.csv')
    with open(task_info_path, 'w') as f:
        f.write(record_total)
    return None
            
            
if __name__=="__main__":
    grandParent = sys.argv[1]
    
    p = Pool(8)
    res_li = []
    
    parents = []
    for parent in os.listdir(grandParent):
        path = os.path.join(grandParent, parent)
        if not os.path.isdir(path):
            continue
        if 'not' in parent:
            continue
        parents.append(path)
    
    parents.sort()
    # parents.reverse()
    ms, ques = [], []
    for parent in parents:
        if 'spb' not in parent:
            continue
        m = Manager()
        que = m.Queue()
        res = p.apply_async(next_msg, (que, parent,))
        res_li.append(res)
        res = p.apply_async(extract, (que, parent,))
        res_li.append(res)
        ms.append(m)
        ques.append(que)
        
    for res in res_li:
        s = res.get()