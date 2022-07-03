from multiprocessing import Pool
import sys
import os
from src.analyzer import event_log
from src.analyzer_local import load_logs_from_dir

net_config = "/Users/jian/Workspace/Research/hongbao-log/configs/bjnj/log-net.json"
spb_config = "/Users/jian/Workspace/Research/hongbao-log/configs/bjnj/log-spb.json"

net_exec_time = (4889246.666, 8059651.437)
# spb_exec_time = (6465674.082, 9447340.816)
spb_exec_time = (6101418.568, 8057716.844)

time_interval = 100 * 1000 * 1000


def check_noise(message_id):
    message_id >>= 40
    return (message_id >> 19) == 1


def check_warm(message_id):
    message_id >>= 40
    message_id = message_id & ((1<<22)-1)
    return message_id < 2


def check_person(message_id):
    device = (message_id>>20) & ((1<<20)-1)
    return device < 4


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


def add2timeline(timeline, ts_start, duration, resource, unit_idx, location, time_interval):
    def add_delta(idx, delta):
        if idx not in timeline:
            # fast_bj, fast_nj, slow_bj, slow_nj
            timeline[idx] = [0, 0, 0, 0]
        timeline[idx][unit_idx*2+location-1] += delta

    ts_end = ts_start + duration - 1
    start_idx = int(ts_start // time_interval)
    end_idx = int(ts_end // time_interval)

    if start_idx == end_idx:
        add_delta(start_idx, resource * duration)
        return
    
    if ts_start % time_interval != 0:
        until_tail = time_interval - (ts_start%time_interval)
        add_delta(start_idx, resource*until_tail)
        start_idx += 1
    
    if (ts_end+1) % time_interval != 0:
        before = ts_end % time_interval
        add_delta(end_idx, resource*before)
        end_idx -= 1
    
    for cur_idx in range(start_idx, end_idx+1):
        add_delta(cur_idx, resource*time_interval)
        

def output_timeline(timeline, filepath):
    f = open(filepath, 'w+')
    for rec in timeline:
        f.write(','.join(map(str, rec))+'\n')
    f.close()


def cal_exec_ave(msg_chains):
    tBjExecTotal = 0
    tNjExecTotal = 0
    noBjRecord = 0
    noNjRecord = 0
    for msg_id, logs in msg_chains:
        if len(logs) < 10: # 没有到 msg svr 发出
            continue
        if check_noise(msg_id) or check_warm(msg_id):
            continue
        ts_start = logs[8].time
        ts_end = logs[9].time
        if get_location(msg_id) == 1:
            tBjExecTotal += ts_end - ts_start
            noBjRecord += 1 
        elif get_location(msg_id) == 2:
            tNjExecTotal += ts_end - ts_start
            noNjRecord += 1
    return tBjExecTotal / noBjRecord, tNjExecTotal / noNjRecord


def calculate_need(parent, env, time_interval):
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
    msg_chains = load_logs_from_dir(log_dirpath, 0)  #type: list[list[(int, event_log)]]

    if env == 'net':
        exec_times = net_exec_time
    if env == 'spb':
        # exec_times = cal_exec_ave(msg_chains)
        # exec_times = spb_exec_time
        exec_times = net_exec_time
    print(env, exec_times)

    timeline: dict[int](int,int) = {} 
    no_task = 0
    for msg_id, logs in msg_chains:
        if get_location(msg_id) > 2:  # invalid message id
            continue
        if len(logs) < 1:  # 没有到 msg svr 发出
            # print('Skip for length')
            continue
        if check_noise(msg_id) or check_warm(msg_id):
            # print(f'Skip for noise:{check_noise(msg_id)} warm:{check_warm(msg_id)}')
            continue
        
        no_task += 1
        qos = get_qos(msg_id)
        location = get_location(msg_id)
        send_time = logs[0].time
        exec_time = exec_times[location-1]
        add2timeline(timeline, send_time, exec_time, 1, 0, location, time_interval)
        add2timeline(timeline, send_time, qos, exec_time / qos, 1, location, time_interval)
    print('==> no_task: ', no_task)

    timeline_list = list(timeline.items())
    timeline_list.sort(key=lambda x: x[0])

    ts_min = timeline_list[0][0]
    ts_max = timeline_list[len(timeline_list)-1][0]

    i_timeline = 0
    finial_timeline = []
    for ts_cur in range(ts_min, ts_max+1):
        # ts, fast_bj, fast_nj, fast_all, slow_bj, slow_nj, slow_all
        record = [ts_cur, 0, 0, 0, 0, 0, 0]
        if ts_cur == timeline_list[i_timeline][0]:
            record[1:3] = timeline_list[i_timeline][1][0:2] # fast
            record[3] = sum(record[1:3])
            record[4:6] = timeline_list[i_timeline][1][2:4] # slow
            record[6] = sum(record[4:6])
            i_timeline += 1
        for i in range(1, 7):
            record[i] = record[i] / time_interval
        finial_timeline.append(record)
    return finial_timeline


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

    timeline = calculate_need(parent, env, time_interval)
    output_timeline(timeline, os.path.join(parent, f"{env}_need_{time_interval//1000000}.csv"))
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
