# scp yuzishu@10.208.104.9:/home/yuzishu/taskswitching/BJ_M2/*.log worker_log/BJ_M2
# scp yuzishu@10.208.104.3:/home/yuzishu/taskswitching/BJ_M1/*.log worker_log/BJ_M1

# scp -P 10002 root@58.240.113.38:/home/yuzishu/taskswitching/NJ_M1/*.log worker_log/NJ_M1
# scp -P 10004 root@58.240.113.38:/home/yuzishu/taskswitching/NJ_M2/*.log worker_log/NJ_M2
import json
import os
import sys
import pprint

time_interval = 100 * 1000 * 1000


def analyze(path, worker_ID):
    files = os.listdir(path)
    total_time = 0
    number = 0
    log_times = {}
    for file in files:
        # print(file)
        if not worker_ID in file:
            continue
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

            msg_ID = subID >> 40
            # print(msg_ID)
            # exit(0)
            if msg_ID == 1 or msg_ID == 2 or msg_ID - (1<<22) == 1 or msg_ID - (1<<22) == 2:
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
    f = open(os.path.join(os.path.dirname(path), os.path.basename(path) + "_analyze.csv"), "w")
    for i in log_times:
        if log_times[i] > max_core:
            max_core = max(max_core, log_times[i])
        f.write(str(i % 1000000) + "," + str(log_times[i]) + "\n")
    print(path, number, total_time, max_core / time_interval)

    f.close()
    return log_times


# path = sys.argv[1]
# interval = sys.argv[2]
def calculate_cpu_usage(path, interval, workerID):
    time_interval = int(interval) * 1000000
    dirs = ["BJ_M1", "BJ_M2", "NJ_M1", "NJ_M2"]
    log_times_total = {}
    log_times_total_detail = {}
    index = 0
    for dir in dirs:
        log_times = analyze(os.path.join(path, dir), workerID)
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
    f = open(path + "/../ts_cpu_usage_{}ms-{}.csv".format(interval, workerID), "w")
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
