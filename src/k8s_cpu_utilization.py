from distutils.command.build_scripts import first_line_re
import os
import sys
from src.analyzer import load_logs_from_dir, list_valid_logs_net
import hashlib


def cal_pos_cpu(path, noise):
    files = os.listdir(path)

    pods_data = []
    for file in files:
        if noise and "noise" not in file:
            continue
        if not noise and "noise" in file:
            continue
        file_path = os.path.join(path, file)
        with open(file_path, "r") as f:
            lines = f.readlines()

        rows = []
        for line in lines:
            if len(line.split(',')) < 2:
                print(line)
                continue
            rows.append(line.split(','))
        if len(rows) == 0:
            continue

        pod_data = []
        # cur_beg = (int(rows[0][1]) // 1000000) % 1000000
        # cur_time = cur_beg
        def takeFirst(elem):
            return int(elem[1])
        rows.sort(key=takeFirst)
        #删除相同时间的
        rows_tmp = [rows[0]]
        for i in range(1, len(rows) - 1):
            if round((int(rows[i][1]) / 1000000))  == round((int(rows[i - 1][1]) / 1000000)) :
                continue
            else:
                rows_tmp.append(rows[i])
        rows = rows_tmp
        #删除由于时间戳和文件读取不同步导致的负数的情况，注意上述问题会导致记录不是ms级精准的，看log应该是10ms级精准
        rows_tmp = [rows[0]]
        for i in range(1, len(rows) - 1):
            if int(rows[i][2]) - int(rows_tmp[-1][2]) < 0:
                continue
            else:
                rows_tmp.append(rows[i])
        rows = rows_tmp
        last_time =  round((int(rows[0][1]) / 1000000))
        for i in range(0, len(rows) - 1):
            cur_time = round((int(rows[i][1]) / 1000000))
            cpu_time = (int(rows[i + 1][2]) - int(rows[i][2])) * 1. / 1000000
            if cpu_time < 0:
                print(path, file, rows[i][1], cpu_time, int(rows[i+1][1]) - int(rows[i][1]))
            else:
                for i in range(last_time + 1, cur_time):
                    pod_data.append([i, 0, 1])
                pod_data.append([cur_time, cpu_time, 1])
                last_time = cur_time


        if len(pod_data) == 0:
            continue
        pods_data.append(pod_data)

    if len(pods_data) == 0:
        return []

    total_data = pods_data[0]
    for i in range(1, len(pods_data)):
        total_data = combine_data(total_data, pods_data[i])

    return total_data


def combine_data(data1, data2):
    if len(data1) == 0:
        return data2
    if len(data2) == 0:
        return data1

    beg_time = data1[0][0] if data1[0][0] < data2[0][0] else data2[0][0]
    end_time = data1[len(data1) - 1][0] if data1[len(data1) - 1][0] > data2[len(data2) - 1][0] else \
    data2[len(data2) - 1][0]

    total_data = [[i, 0, 0] for i in range(beg_time, end_time + 1)]
    try:
        for row in data1:
            time = row[0]
            cpu_time = row[1]
            pod_num = row[2]
            idx = time - beg_time
            total_data[idx][1] += cpu_time
            total_data[idx][2] += pod_num
    except Exception as err:
        print(idx, beg_time, end_time)
    for row in data2:
        time = row[0]
        cpu_time = row[1]
        pod_num = row[2]
        idx = time - beg_time
        total_data[idx][1] += cpu_time
        total_data[idx][2] += pod_num

    return total_data


def compress_final_data(data, time_interval):
    beg_time = data[0][0] // time_interval
    end_time = data[len(data) - 1][0] // time_interval

    total_data = [[i, 0, 0, 0, 0, 0, 0] for i in range(beg_time, end_time + 1)]
    for row in data:
        time = row[0] // time_interval
        idx = time - beg_time

        bj_cpu_time = row[1]
        nj_cpu_time = row[3]
        all_cpu_time = row[5]

        bj_pod_num = row[2]
        nj_pod_num = row[4]

        if idx >= len(total_data):
            print(time_interval)
            print(data[0])
            print(data[len(data)-1])
            print(row)
            print(beg_time, end_time)
        total_data[idx][1] += bj_cpu_time
        total_data[idx][3] += nj_cpu_time
        total_data[idx][5] += all_cpu_time

        total_data[idx][2] = bj_pod_num if bj_pod_num > total_data[idx][2] else total_data[idx][2]
        total_data[idx][4] = nj_pod_num if bj_pod_num > total_data[idx][4] else total_data[idx][4]
        total_data[idx][6] = total_data[idx][2] + total_data[idx][4]

    return total_data


def compress_final_data_machine(data, time_interval):
    beg_time = data[0][0] // time_interval
    end_time = data[len(data) - 1][0] // time_interval

    total_data = [[i, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] for i in range(beg_time, end_time + 1)]
    for row in data:
        time = row[0] // time_interval
        idx = time - beg_time

        bj3_cpu_time = row[1]
        bj9_cpu_time = row[3]
        nj4_cpu_time = row[5]
        nj5_cpu_time = row[7]

        bj3_pod_num = row[2]
        bj9_pod_num = row[4]
        nj4_pod_num = row[6]
        nj5_pod_num = row[8]

        total_data[idx][1] += bj3_cpu_time
        total_data[idx][3] += bj9_cpu_time
        total_data[idx][5] += nj4_cpu_time
        total_data[idx][7] += nj5_cpu_time
        total_data[idx][9] = total_data[idx][1] + total_data[idx][3] + total_data[idx][5] + total_data[idx][7]

        total_data[idx][2] = bj3_pod_num if bj3_pod_num > total_data[idx][2] else total_data[idx][2]
        total_data[idx][4] = bj9_pod_num if bj9_pod_num > total_data[idx][4] else total_data[idx][4]
        total_data[idx][6] = nj4_pod_num if nj4_pod_num > total_data[idx][6] else total_data[idx][6]
        total_data[idx][8] = nj5_pod_num if nj5_pod_num > total_data[idx][8] else total_data[idx][8]
        total_data[idx][10] = total_data[idx][2] + total_data[idx][4] + total_data[idx][6] + total_data[idx][8]

    return total_data


def get_first_time(dirpath):
    log_dirname = ""
    contents = os.listdir(os.path.join(dirpath, "../"))
    for content in contents:
        if "2022" in content:
            log_dirname = content
            break
    if log_dirname == "":
        print("no log dir")
        return
    print("log_dirname:", log_dirname)

    log_data_sorted = load_logs_from_dir(os.path.join(dirpath, "../" + log_dirname), 0)
    valid_logs = list_valid_logs_net(log_data_sorted)
    print("valid_logs length:", len(valid_logs))

    first_time_full = 999999999999999999999
    for log_item in valid_logs:
        logs = log_item[1]
        if logs[0].time < first_time_full:
            first_time_full = logs[0].time

    return (first_time_full // 1000000)


def list_total_cput_each_machine(dirpath, noise):
    dirs = ["lab3n", "lab9", "hbnj4"]
    if os.path.exists(os.path.join(dirpath, 'hbnj3')):
        dirs.append('hbnj3')
    else:
        dirs.append('hbnj5')

    pos_data = []
    for dir in dirs:
        sub_path = os.path.join(dirpath, dir)
        item = cal_pos_cpu(sub_path, noise)
        pos_data.append(item)

    bj_data = combine_data(pos_data[0], pos_data[1])
    nj_data = combine_data(pos_data[2], pos_data[3])

    all_data = combine_data(bj_data, nj_data)
    if len(all_data) == 0:
        return []

    beg_time = all_data[0][0]
    end_time = all_data[len(all_data) - 1][0]

    final_data = [[i, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] for i in range(beg_time, end_time + 1)]
    for i_pos, pos_d in enumerate(pos_data):
        for row in pos_d:
            time = row[0]
            idx = time - beg_time
            final_data[idx][2*i_pos+1:2*i_pos+3] = row[1:3]
    for row in all_data:
        time = row[0]
        idx = time - beg_time
        final_data[idx][9:11] = row[1:3]
    return final_data


def list_total_cpu(dirpath, noise):
    dirs = ["lab3n", "lab9", "hbnj4", "hbnj3"]
    pos_data = []
    for dir in dirs:
        sub_path = os.path.join(dirpath, dir)
        item = cal_pos_cpu(sub_path, noise)
        pos_data.append(item)

    bj_data = combine_data(pos_data[0], pos_data[1])
    nj_data = combine_data(pos_data[2], pos_data[3])

    all_data = combine_data(bj_data, nj_data)
    if len(all_data) == 0:
        return []

    beg_time = all_data[0][0]
    end_time = all_data[len(all_data) - 1][0]

    final_data = [[i, 0, 0, 0, 0, 0, 0] for i in range(beg_time, end_time + 1)]
    for row in bj_data:
        time = row[0]
        idx = time - beg_time
        final_data[idx][1:3] = row[1:3]
    for row in nj_data:
        time = row[0]
        idx = time - beg_time
        final_data[idx][3:5] = row[1:3]
    for row in all_data:
        time = row[0]
        idx = time - beg_time
        final_data[idx][5:7] = row[1:3]

    return final_data


def filter_data(data, f):
    filtered = []
    for row in data:
        if f(row):
            filtered.append(row)
    return filtered


def write_file(data, file_name):
    with open(file_name, "w") as f:
        for row in data:
            row[0] = row[0]
            txt = ','.join(map(str, row)) + '\n'
            # txt = "{},{},{},{},{},{},{}\n".format(row[0], row[1], row[2], row[3], row[4], row[5], row[6])
            f.write(txt)


def cal_summary(data):
    if len(data) == 0:
        return [0] * 7

    sum = [0] * 6
    for row in data:
        for i in range(6):
            sum[i] += row[i+1]

    summary = [0] * 7
    for i in range(6):
        summary[i] = sum[i] / len(data)
    summary[6] = summary[4] / summary[5]
    return summary


def analyze_machine(dirpath, noise):
    flag = "noise" if noise else "load"

    total_date = list_total_cput_each_machine(dirpath, noise)
    print("total_data length:", len(total_date))
    if len(total_date) == 0:
        print("no such data: ", dirpath, noise)
        return

    first_time = get_first_time(dirpath)
    print("first_time: ", first_time)

    # total 1ms
    print("cal k8s cpu alloc 1ms ......")
    filtered_data = filter_data(total_date,
                                lambda log: 0 <= log[0] < first_time + 20000000)
    write_file(filtered_data, dirpath + "/../k8s_machine_{}_cpu_1ms.csv".format(flag))
    # summary2 = cal_summary(filtered_data)

    # total 100ms
    resolution = 100
    print("cal k8s cpu alloc %dms ......"%resolution)
    compressed_data = compress_final_data_machine(total_date, resolution)
    filtered_data = filter_data(compressed_data,
                                lambda log: 0 // resolution <= log[0] < (first_time + 20000000) // resolution)
    suffix = hashlib.md5(dirpath.encode('utf-8')).hexdigest()[:6]
    write_file(filtered_data, dirpath + f"/../k8s_machine_{flag}_cpu_{resolution}ms-{suffix}.csv")
    # summary3 = cal_summary(filtered_data)

    # summary_file = open(dirpath + "/../k8s_{}_cpu_summary.csv".format(flag), "w")
    # # summary_file.write("20_20.5," + ','.join(map(str, summary1)) + "\n")
    # summary_file.write("1ms," + ','.join(map(str, summary2)) + "\n")
    # summary_file.write("100ms," + ','.join(map(str, summary3)) + "\n")
    # summary_file.close()


def analyze(dirpath, noise):
    flag = "noise" if noise else "load"

    total_date = list_total_cpu(dirpath, noise)
    print("total_data length:", len(total_date))
    if len(total_date) == 0:
        print("no such data: ", dirpath, noise)
        return

    first_time = get_first_time(dirpath)
    print("first_time: ", first_time)

    # 20-20.5
    # print("cal k8s cpu alloc 20-20.5 ......")
    # filtered_data = filter_data(total_date,
    #                             lambda log: first_time + 20 * 1000 < log[0] <= first_time + 20.5 * 1000)
    # write_file(filtered_data, dirpath + "/../k8s_{}_cpu_20-20.5.csv".format(flag))
    # summary1 = cal_summary(filtered_data)

    # total 1ms
    print("cal k8s cpu alloc 1ms ......")
    filtered_data = filter_data(total_date,
                                lambda log: 0 <= log[0] < first_time + 20000000)
    write_file(filtered_data, dirpath + "/../k8s_{}_cpu_1ms.csv".format(flag))
    summary2 = cal_summary(filtered_data)

    # total 100ms
    resolution = 100
    print("cal k8s cpu alloc %dms ......"%resolution)
    compressed_data = compress_final_data(total_date, resolution)
    filtered_data = filter_data(compressed_data,
                                lambda log: 0 // resolution <= log[0] < (first_time + 20000000) // resolution)
    write_file(filtered_data, dirpath + f"/../k8s_{flag}_cpu_{resolution}ms.csv")
    summary3 = cal_summary(filtered_data)

    summary_file = open(dirpath + "/../k8s_{}_cpu_summary.csv".format(flag), "w")
    # summary_file.write("20_20.5," + ','.join(map(str, summary1)) + "\n")
    summary_file.write("1ms," + ','.join(map(str, summary2)) + "\n")
    summary_file.write("100ms," + ','.join(map(str, summary3)) + "\n")
    summary_file.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("k8s_cpu_utilization.py K8s-CPU-dir")
        exit(1)

    path = sys.argv[1]

    # analyze(path, False)
    # analyze(path, True)

    analyze_machine(path, False)
