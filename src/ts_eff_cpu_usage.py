# scp yuzishu@10.208.104.9:/home/yuzishu/taskswitching/BJ_M2/*.log worker_log/BJ_M2
# scp yuzishu@10.208.104.3:/home/yuzishu/taskswitching/BJ_M1/*.log worker_log/BJ_M1

# scp -P 10002 root@58.240.113.38:/home/yuzishu/taskswitching/NJ_M1/*.log worker_log/NJ_M1
# scp -P 10004 root@58.240.113.38:/home/yuzishu/taskswitching/NJ_M2/*.log worker_log/NJ_M2
import json
import os
from re import sub
import sys
import pprint
from calculate_need_usage_alloc import load_comp_ranges, get_mac_parent
import hashlib
from calculate_need import check_noise, check_warm, get_location, check_person, get_qos

time_interval = 100 * 1000 * 1000

def load_task_info(parent):
    mac_parent = get_mac_parent(parent)
    suffix = hashlib.md5(mac_parent.encode('utf-8')).hexdigest()[:6]
    task_info_path = os.path.join(parent, f'task-info-{suffix}.csv')
    task_infos = {}
    with open(task_info_path, 'r') as f:
        for line in f:
            line = line.strip()
            parts = line.split(',')
            message_id = int(parts[0])
            is_good = parts[4] == 'True'
            task_infos[message_id] = is_good
    return task_infos

def analyze(path, task_infos):
    files = os.listdir(path)
    total_time = 0
    number = 0
    log_times = {}
    for file in files:
        # print(file)
        if file == "analyze.json" or file == "analyze.csv" or file == ".DS_Store":
            continue
        file_path = os.path.join(path, file)
        f = open(file_path)
        lines = f.readlines()
        
        for line in lines:
            log = line.split(",")
            if len(log) < 4 or log[0] == '':
                continue
            subID = int(log[0].split("_")[-1])

            if check_noise(subID) or check_warm(subID) or check_person(subID):
                continue

            is_good = task_infos[subID]
            if not is_good:
                continue

            start_time = int(log[2])
            end_time = int(log[3])
            time = end_time - start_time + 1

            start_seconds = start_time // time_interval
            end_seconds = end_time // time_interval

            for i in range(start_seconds, end_seconds + 1):
                if end_seconds > i > start_seconds:
                    time_tmp = time_interval
                elif i == start_seconds:
                    if end_time > (start_seconds + 1) * time_interval:
                        time_tmp = (start_seconds + 1) * time_interval - start_time
                    else:
                        time_tmp = end_time - start_time
                elif i == end_seconds:
                    time_tmp = end_time - end_seconds * time_interval

                if log_times.__contains__(i):
                    log_times[i] += time_tmp
                else:
                    log_times[i] = time_tmp
            total_time += time
            number += 1
        f.close()

    # print(os.path.basename(path))
    max_core = 0
    f = open(os.path.join(os.path.dirname(path), os.path.basename(path) + "_eff_analyze.csv"), "w")
    for i in log_times:
        if log_times[i] > max_core:
            max_core = max(max_core, log_times[i])
        f.write(str(i % 1000000) + "," + str(log_times[i]) + "\n")
    print(path, number, total_time, max_core / time_interval)

    f.close()
    return log_times


parent = sys.argv[1]
interval = sys.argv[2]
time_interval = int(interval) * 1000000

task_infos = load_task_info(parent)

path = os.path.join(parent, 'ts-cpu')
dirs = ["BJ_M1", "BJ_M2", "NJ_M1", "NJ_M2"]
log_times_total = {}
log_times_total_detail = {}
index = 0
for dir in dirs:
    log_times = analyze(os.path.join(path, dir), task_infos)
    for i in log_times:
        if log_times_total.__contains__(i):
            log_times_total[i] += log_times[i]
        else:
            log_times_total[i] = log_times[i]
        if log_times_total_detail.__contains__(i):
            log_times_total_detail[i][index] = log_times[i]
        else:
            log_times_total_detail[i] = [0, 0, 0, 0]
            log_times_total_detail[i][index] = log_times[i]
    index += 1

max_core = 0
min_core = 38292303
for i in log_times_total:
    max_core = max(max_core, log_times_total[i])
    if min_core > log_times_total[i]:
        min_core = min(min_core, log_times_total[i])

# pprint.pprint(log_times_total)
f = open(path + "/../ts_eff_cpu_usage_{}ms.csv".format(interval), "w")
keys = list(log_times_total_detail.keys())
keys.sort()
start = keys[0]
end = keys[-1]
for i in range(start, end):
    total_time = 0
    f.write(str(i % 1000000) + ",")
    if log_times_total_detail.__contains__(i):
        for core_usage in log_times_total_detail[i]:
            total_time += core_usage / time_interval
            f.write(str(core_usage / time_interval) + ",")
    else:
        f.write("0,0,0,0,")
    f.write(str(total_time) + ",")
    f.write("\n")
f.close()
