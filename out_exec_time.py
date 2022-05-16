from multiprocessing import Pool
import sys
import os
from src.analyzer import event_log
from src.analyzer_local import load_logs_from_dir

net_config = "/Users/jian/Workspace/Research/hongbao-log/configs/bjnj/log-net.json"
spb_config = "/Users/jian/Workspace/Research/hongbao-log/configs/bjnj/log-spb.json"

time_interval = 100 * 1000 * 1000


def check_noise(message_id):
    message_id >>= 40
    return (message_id >> 19) == 1


def check_warm(message_id):
    message_id >>= 40
    return message_id < 2


def get_location(message_id):
    return message_id & ((1<<20)-1)


# TODO： qos确认
def get_qos(total_id):
    location = get_location(total_id)
    message_id = total_id >> 40
    if location == 1:
        if message_id % 2 == 0:
            return 100000000
        if  message_id % 2 == 1:
            return 50000000
    elif location == 2:
        if message_id % 2 == 0:
            return 100000000
        if  message_id % 4 == 1:
            return 50000000
        if  message_id % 4 == 3:
            return 20000000
    else:
        print('Invalid message id, ', total_id)
    return -1


def check_net_6(logs: list[event_log]):
    if len(logs) != 6:
        return False
    return logs[5].logger.strip() == 'Wang'


def check_net_8(logs: list[event_log]):
    if len(logs) != 8:
        return False
    return True


def check_spb_14(logs: list[event_log]):
    if len(logs) != 14:
        return False
    return True


def output(exec_times, filepath):
    print(filepath)
    with open(filepath, 'w') as f:
        f.write(','.join(['msg_id', 'location', 'ts_start', 'ts_end', 'exec'])+'\n')
        for exec_time in exec_times:
            f.write(','.join(map(str, exec_time))+'\n')


def process_exec_time(parent, env):
    log_dirpath = None
    for file in os.listdir(parent):
        if not os.path.isdir(os.path.join(parent, file)):
            continue
        if file.startswith('2022'):
            log_dirpath = os.path.join(parent, file)
            break
    if log_dirpath is None:
        print('Not found log dirpath')
        return []
    msg_chains = load_logs_from_dir(log_dirpath, 0)  #type: list[(int, list[event_log])]

    exec_times = []
    for msg_id, logs in msg_chains:
        if check_noise(msg_id) or check_warm(msg_id):
            continue
        
        location = get_location(msg_id)
        ts_start = -1
        ts_end = -1
        if env == 'net':
            if check_net_6(logs):
                ts_start = logs[2].time
                ts_end = logs[3].time
            elif check_net_8(logs):
                ts_start = logs[2].time
                ts_end = logs[3].time
        elif env == 'spb':
            if check_spb_14(logs):
                ts_start = logs[8].time
                ts_end = logs[9].time
        
        if ts_start != -1:
            exec_times.append((msg_id, location, ts_start, ts_end, ts_end - ts_start))
    
    return exec_times


def calculate_one(parent):
    if not os.path.isdir(parent):
        return 0
    if "net" in parent:
        env = 'net'
    elif "spb" in parent:
        env = 'spb'
    else:
        print('dir is wrong')
        return 0

    exec_times = process_exec_time(parent, env)
    if len(exec_times) == 0:
        return 0
    output(exec_times, os.path.join(parent, 'exec_time.csv'))
    return 0
    

if __name__=="__main__":
    grandParent = sys.argv[1]
    
    parents = []
    for parent in os.listdir(grandParent):
        path = os.path.join(grandParent, parent)
        if not os.path.isdir(path):
            continue
        # if "spb" in parent:
        #     continue
        parents.append(path)
    
    p = Pool(8)
    res_li = []
    for parent in parents:
        res = p.apply_async(calculate_one, (parent,))
        res_li.append(res)
    for res in res_li:
        res.get()
