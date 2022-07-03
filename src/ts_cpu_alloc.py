import sys

from src.analyzer import list_valid_logs_spb, load_logs_from_dir

machines = ["BJ-Machn-0", "BJ-Machn-1", "NJ-Machn-0", "NJ-Machn-1"]


def list_task_duration(log_data_sorted):
    valid_logs = list_valid_logs_spb(log_data_sorted)
    time_sum = {}
    for log_item in valid_logs:
        logs = log_item[1]
        for i in range(len(logs)):
            log = logs[i]
            duration = logs[i + 2].time - logs[i + 1].time
            start_time = logs[i + 1].time
            end_time = logs[i + 2].time
            if log.logger in machines:
                if log.logger not in time_sum:
                    time_sum[log.logger] = []
                time_sum[log.logger].append([duration, start_time, end_time])
                break
    return time_sum


def cal_cpu_alloc(pos_task_logs, time_interval=100 * 1000 * 1000):
    log_times = {}
    for log in pos_task_logs:
        start_time = int(log[1])
        end_time = int(log[2])

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
    return log_times


def write_file(data, output_filepath):
    with open(output_filepath, "w") as f:
        for row in data:
            f.write(','.join(map(str, row)) + "\n")


def analyze(machine_task_duration, time_interval):
    log_times_total = {}
    log_times_total_detail = {}
    for idx, machine in enumerate(machines):
        if not machine_task_duration.__contains__(machine):
            continue
        log_times = cal_cpu_alloc(machine_task_duration[machine], time_interval)
        for i in log_times:
            if log_times_total.__contains__(i):
                log_times_total[i] += log_times[i]
            else:
                log_times_total[i] = log_times[i]
            if log_times_total_detail.__contains__(i):
                log_times_total_detail[i][idx] = log_times[i]
            else:
                log_times_total_detail[i] = [0, 0, 0, 0]
                log_times_total_detail[i][idx] = log_times[i]

    keys = list(log_times_total_detail.keys())
    keys.sort()
    start = keys[0]
    end = keys[-1]

    total_data = []
    for i in range(start, end + 1):
        total_time = 0
        row = [i % 1000000]
        if log_times_total_detail.__contains__(i):
            for core_usage in log_times_total_detail[i]:
                total_time += core_usage / time_interval
                row.append(core_usage / time_interval)
        else:
            row.extend([0, 0, 0, 0])
        row.append(total_time)
        total_data.append(row)

    return total_data


def cal_summary(data):
    sum = [0] * 5
    for row in data:
        for i in range(5):
            sum[i] += row[i+1]

    summary = [0] * 5
    for i in range(5):
        summary[i] = sum[i] / len(data)
    return summary


def filter_data(data, f):
    filtered = []
    for row in data:
        if f(row):
            filtered.append(row)
    return filtered


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("ts_cpu_alloc.py TS-LOG-DIR")
        exit(1)

    dir_path = sys.argv[1]

    log_data_sorted = load_logs_from_dir(dir_path, 0)
    print(len(log_data_sorted))
    machine_task_duration = list_task_duration(log_data_sorted)

    print("cal ts cpu alloc 100ms ......")
    alloc_100 = dir_path + "/../ts_cpu_alloc_100ms.csv"
    total_data_100ms = analyze(machine_task_duration, 100 * 1000 * 1000)
    write_file(total_data_100ms, alloc_100)
    summary3 = cal_summary(total_data_100ms)

    print("cal ts cpu alloc 1ms ......")
    alloc_1 = dir_path + "/../ts_cpu_alloc_1ms.csv"
    total_data_1ms = analyze(machine_task_duration, 1000 * 1000)
    write_file(total_data_1ms, alloc_1)
    summary1 = cal_summary(total_data_1ms)

    first_time = total_data_1ms[0][0]

    print("cal ts cpu alloc 20-20.5 ......")
    # data_20_20d5 = filter_data(total_data_1ms, lambda log: first_time + 20000 < log[0] < first_time + 20500)
    # print(len(data_20_20d5))
    # write_file(data_20_20d5, dir_path + "/../ts_cpu_alloc_20_20.5.csv")
    # summary2 = cal_summary(data_20_20d5)

    summary_file = open(dir_path + "/../ts_cpu_alloc_summary.csv", "w")
    summary_file.write("1ms," + ','.join(map(str, summary1)) + "\n")
    # summary_file.write("20_20.5," + ','.join(map(str, summary2)) + "\n")
    summary_file.write("100ms," + ','.join(map(str, summary3)) + "\n")
    summary_file.close()

