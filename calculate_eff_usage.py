import os
from out_exec_time import check_noise, check_warm, check_net_6, check_net_8, check_spb_14
from calculate_need import get_qos, get_location, net_exec_time, check_person
from src.analyzer import event_log
from src.analyzer_local import load_logs_from_dir


def add2timeline(timeline, ts_start, duration, resource, location, time_interval):
    def add_delta(idx, delta):
        if idx not in timeline:
            # eff_bj, eff_nj
            timeline[idx] = [0, 0]
        timeline[idx][location-1] += delta

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


def calculate_eff_usage(parent, env, time_interval):
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

    timeline = {}
    for msg_id, logs in msg_chains:
        if check_noise(msg_id) or check_warm(msg_id) or check_person(msg_id):
            continue
        
        ts_start = -1
        ts_end = -1
        if env == 'net':
            if check_net_6(logs):
                ts_start = logs[1].time
                ts_end = logs[4].time
            elif check_net_8(logs):
                ts_start = logs[1].time
                ts_end = logs[6].time
        elif env == 'spb':
            if check_spb_14(logs):
                ts_start = logs[1].time
                ts_end = logs[12].time
        if ts_start == -1:
            continue

        qos = get_qos(msg_id)
        if ts_end > ts_start + qos:
            continue
        
        location = get_location(msg_id)
        need_time = net_exec_time[location-1]
        resp_time = ts_end - ts_start - 1

        add2timeline(timeline, ts_start, resp_time, need_time/resp_time, location, time_interval)

    timeline_list = list(timeline.items())
    timeline_list.sort(key=lambda x: x[0])

    ts_min = timeline_list[0][0]
    ts_max = timeline_list[len(timeline_list)-1][0]

    i_timeline = 0
    finial_timeline = []
    for ts_cur in range(ts_min, ts_max+1):
        # ts, eff_bj, eff_nj, eff_all
        record = [ts_cur, 0, 0, 0]
        if ts_cur == timeline_list[i_timeline][0]:
            record[1:3] = timeline_list[i_timeline][1][0:2]
            record[3] = sum(record[1:3])
            i_timeline += 1
        for i in range(1, 4):
            record[i] = record[i] / time_interval
        finial_timeline.append(record)
    return finial_timeline