"""

计算熵


概要过程：

`calculate_one`函数针对一次实验进行分析，首先以`time_interval`为时间间隔，对CPU的分配、使用情况进行统计，构建时间线

然后调用用于分析时间线的函数，前后有多个版本，最终是`build_str_entropy`，在该函数中计算 从需求发起到需求结束 和 从需求发起到结束分配 两个时间段的熵，计算熵的版本最终为`get_an_ua_eu_en_entropy_v7`函数。两时段的计算方法相同，只是时间范围不同，确定时间范围对应的是`find_need_range`和`find_alloc_range`两个函数。

最终会输出一个以逗号为分割，包含任务信息、熵、通量、良率等信息的字符串，并由`calculate_one`返回至主函数


使用方法：

python3 calculate_need_usage_alloc.py <日志数据根目录>

例：python3 calculate_need_usage_alloc.py /Volumes/Elements/logs-yuzishu-5-4-k8s-peak-50-speed-1

在目录中会输出一个csv文件，文件名在main函数中设定


"""

import hashlib
import json
import math
from multiprocessing import Pool, Lock
import sys
import os
import re
from time import time
import numpy as np

from calculate_need import calculate_need, check_noise, check_warm, get_location, check_person
from src.k8s_cpu_utilization import list_total_cpu, compress_final_data
from calculate_eff_usage import calculate_eff_usage
from src.analyzer_local import load_logs_from_dir, msg_id_dot2int
from src.analyzer import event_log
from out_exec_time import check_net_6, check_net_8, check_spb_14, get_qos


time_interval = 100 * 1000 * 1000
lock = Lock()

def get_mac_parent(parent):
    ret = parent
    ret = ret.replace('/Users/jian/logs', '/Volumes/Elements')
    ret = ret.replace('/mnt/g', '/Volumes/Elements')
    ret = ret.replace('/mnt/e/zsj/logs', '/Volumes/Elements')
    ret = ret.replace('/mnt/e', '/Volumes/Elements')
    ret = ret.replace('/mnt/f', '/Volumes/Elements')
    return ret

def get_k8s_req_lim(parent):
    grps = re.search(r'([0-9m]+)C(.*)C', parent)
    s_request = grps.group(1)
    s_limit = grps.group(2)
    if s_request == '10m':
        request = 0.01
    else:
        request = int(s_request)
    limit = int(s_limit)
    return request, limit


def calculate_usage_alloc(env, parent, time_interval):
    if env == 'net':
        request, limit = get_k8s_req_lim(parent)

        cpu_dirpath = os.path.join(parent, 'k8s-cpu')
        total_date = list_total_cpu(cpu_dirpath, noise=False)
        if len(total_date) == 0:
            return []
        ini_timeline = compress_final_data(
            total_date, time_interval // 1000000)

        timeline = []
        for unit in ini_timeline:
            record = [0, 0, 0, 0, 0, 0, 0]
            record[0] = unit[0]
            record[1:4] = unit[2], unit[4], unit[6]
            record[4:7] = unit[1], unit[3], unit[5]

            record[1:4] = map(lambda x: x * request, record[1:4])
            record[4:7] = map(
                lambda x: x / (time_interval//1000000), record[4:7])

            timeline.append(record)
        ini_timeline = None

    else:
        # 读取使用CPU
        filename = f'ts_cpu_usage_{time_interval//1000000}ms-99999998.csv'
        filepath = os.path.join(parent, filename)
        if not os.path.exists(filepath):
            filename = f'ts_cpu_usage_{time_interval//1000000}ms.csv'
            filepath = os.path.join(parent, filename)
            if not os.path.exists(filepath):
                return []

        usage_timeline = []
        with open(filepath, 'r') as f:
            rows = f.read().strip().split('\n')
            for row in rows:
                cols = row.strip().split(',')
                cols = cols[:7]
                cols[0] = int(cols[0])
                for i in range(1, 7):
                    if len(cols[i]) > 0:
                        cols[i] = float(cols[i])
                    else:
                        cols[i] = 0

                record = [0, 0, 0, 0]
                record[0] = cols[0]
                record[1] = sum(cols[1:3])
                record[2] = sum(cols[3:5])
                record[3] = sum(cols[5:7])
                usage_timeline.append(record)

        # 读取分配CPU
        filename = f'ts_cpu_alloc_{time_interval//1000000}ms.csv'
        filepath = os.path.join(parent, filename)
        if not os.path.exists(filepath):
            return []

        alloc_timeline = []
        with open(filepath, 'r') as f:
            rows = f.read().strip().split('\n')
            for row in rows:
                cols = row.strip().split(',')
                cols[0] = int(cols[0])
                cols[1:] = map(float, cols[1:])

                record = [0, 0, 0, 0]
                record[0] = cols[0]
                record[1] = sum(cols[1:3])
                record[2] = sum(cols[3:5])
                record[3] = sum(cols[5:7])
                alloc_timeline.append(record)

        i_usage = 0
        i_alloc = 0
        timeline = []
        while i_usage < len(usage_timeline) and i_alloc < len(alloc_timeline):
            # ts, alloc_bj, alloc_nj, alloc_total, usage_bj, usage_nj, usage_total
            record = [0, 0, 0, 0, 0, 0, 0]
            if usage_timeline[i_usage][0] < alloc_timeline[i_alloc][0]:
                record[0] = usage_timeline[i_usage][0]
                record[4:7] = usage_timeline[i_usage][1:4]
                i_usage += 1
            elif usage_timeline[i_usage][0] > alloc_timeline[i_alloc][0]:
                record[0] = alloc_timeline[i_alloc][0]
                record[1:4] = alloc_timeline[i_alloc][1:4]
                i_alloc += 1
            else:
                record[0] = usage_timeline[i_usage][0]
                record[1:4] = alloc_timeline[i_alloc][1:4]
                record[4:7] = usage_timeline[i_usage][1:4]
                i_usage += 1
                i_alloc += 1
            timeline.append(record)
        while i_usage < len(usage_timeline):
            # ts, alloc_bj, alloc_nj, alloc_total, usage_bj, usage_nj, usage_total
            record = [0, 0, 0, 0, 0, 0, 0]
            record[0] = usage_timeline[i_usage][0]
            record[4:7] = usage_timeline[i_usage][1:4]
            i_usage += 1
            timeline.append(record)
        while i_alloc < len(alloc_timeline):
            # ts, alloc_bj, alloc_nj, alloc_total, usage_bj, usage_nj, usage_total
            record = [0, 0, 0, 0, 0, 0, 0]
            record[0] = alloc_timeline[i_alloc][0]
            record[1:4] = alloc_timeline[i_alloc][1:4]
            i_alloc += 1
            timeline.append(record)
    return timeline


def calculate_usage(env, parent, time_interval):
    if env == 'net':
        cpu_dirpath = os.path.join(parent, 'k8s-cpu')
        total_date = list_total_cpu(cpu_dirpath, noise=False)
        timeline = compress_final_data(total_date, time_interval // 1000000)
    else:
        filename = f'ts_cpu_usage_{time_interval//1000000}ms.csv'
        filepath = os.path.join(parent, filename)
        timeline = []
        with open(filepath, 'r') as f:
            rows = f.read().strip().split('\n')
            for row in rows:
                cols = row.strip().split(',')
                cols[0] = int(cols[0])
                cols[1:] = map(float, cols[1:])
                timeline.append(cols)
    return timeline


def output_timeline(timeline, filepath):
    f = open(filepath, 'w+')
    f.write('ts,need_fast_bj,need_fast_nj,need_fast_all,need_slow_bj,need_slow_nj,need_slow_all,alloc_bj,alloc_nj,alloc_all,usage_bj,usage_nj,usage_all,eff_bj,eff_nj,eff_all,eff_ne_bj,eff_ne_nj,eff_ne_all\n')
    for rec in timeline:
        f.write(','.join(map(str, rec))+'\n')
    f.close()


def get_yield(parent):
    for dir in os.listdir(parent):
        if not dir.startswith('2022'):
            continue
        filepath = os.path.join(parent, f'{dir}/result.csv')
        if not os.path.exists(filepath):
            break
        with open(filepath, 'r') as f:
            parts = f.read().split(',')
            return parts[4]
    return -1


def load_yld_machs(parent):
    if os.path.exists(os.path.join(parent, '../yld_machs.json')):
        with open(os.path.join(parent, '../yld_machs.json'), 'r') as f:
            return json.load(f)
    return {}

def dump_yld_machs(parent, data):
    with open(os.path.join(parent, '../yld_machs.json'), 'w') as f:
        json.dump(data, f, indent=2)


def get_msg_mach_yield(parent):
    with lock:
        yld_machs = load_yld_machs(parent)
    mac_parent = get_mac_parent(parent)    
    if mac_parent in yld_machs:
        return yld_machs[mac_parent]

    log_dirpath = None
    for file in os.listdir(parent):
        if not os.path.isdir(os.path.join(parent, file)):
            continue
        if file.startswith('2022'):
            log_dirpath = os.path.join(parent, file)
            break
    if log_dirpath is None:
        print(parent, 'Not found log dirpath')
        return -1
    msg_chains = load_logs_from_dir(log_dirpath, 0)

    SPB_LEN = 14
    SPB_START_IDX = 2
    SPB_END_IDX = SPB_LEN - 4

    # get average communication latency
    comm_lat_total = 0
    comm_lat_no = 0
    for msg_id, logs in msg_chains:
        if check_warm(msg_id) or check_person(msg_id) or check_noise(msg_id):
            continue
        if not check_spb_14(logs):
            continue
        
        comp_in_bj = False
        if logs[SPB_END_IDX].logger == "BJ-Machn-0" or \
                logs[SPB_END_IDX].logger == "BJ-Machn-1":
            comp_in_bj = True
        if comp_in_bj:
            continue

        comm_lat = logs[SPB_END_IDX+1].time - logs[SPB_END_IDX].time
        if comm_lat > 100 * 1000 * 1000:
            continue
        comm_lat_total += comm_lat
        comm_lat_no += 1
    comm_lat_ave = comm_lat_total / comm_lat_no

    no_good = 0
    no_task = 0
    for msg_id, logs in msg_chains:
        if check_warm(msg_id) or check_person(msg_id) or check_noise(msg_id):
            continue
        no_task += 1
        if not check_spb_14(logs):
            continue
        
        comp_in_bj = False
        if logs[SPB_END_IDX].logger == "BJ-Machn-0" or \
                logs[SPB_END_IDX].logger == "BJ-Machn-1":
            comp_in_bj = True

        duration = logs[SPB_END_IDX].time - logs[SPB_START_IDX].time
        if comp_in_bj == 1:
            duration += comm_lat_ave
        
        qos = get_qos(msg_id)
        if duration < qos:
            no_good += 1

    yld = no_good / no_task
    with lock:
        yld_machs = load_yld_machs(parent)
        yld_machs[mac_parent] = yld
        dump_yld_machs(parent, yld_machs)
    return yld


def get_goodput(parent):
    for dir in os.listdir(parent):
        if not dir.startswith('2022'):
            continue
        filepath = os.path.join(parent, f'{dir}/result.csv')
        if not os.path.exists(filepath):
            break
        with open(filepath, 'r') as f:
            parts = f.read().strip().split(',')
            return sum(map(float, parts[7:]))
    return -1

def calculate_eff_ne_usage(parent, env, time_interval, eff_timeline):
    eff_ne_timeline = []
    
    if env == 'net':
        for unit in eff_timeline:
            eff_ne_timeline.append([unit[0], 0, 0, 0])
        return eff_ne_timeline
    
    filename = f'ts_eff_cpu_usage_{time_interval//1000000}ms-99999998.csv'
    filepath = os.path.join(parent, filename)
    if not os.path.exists(filepath):
        filename = f'ts_eff_cpu_usage_{time_interval//1000000}ms.csv'
        filepath = os.path.join(parent, filename)
        if not os.path.exists(filepath):
            return []
    
    with open(filepath, 'r') as f:
        rows = f.read().strip().split('\n')
        for row in rows:
            cols = row.strip().split(',')
            cols = cols[:7]
            cols[0] = int(cols[0])
            for i in range(1, 7):
                if len(cols[i]) > 0:
                    cols[i] = float(cols[i])
                else:
                    cols[i] = 0

            record = [0, 0, 0, 0]
            record[0] = cols[0]
            record[1] = sum(cols[1:3])
            record[2] = sum(cols[3:5])
            record[3] = sum(cols[5:7])
            eff_ne_timeline.append(record)
    return eff_ne_timeline
    
def read_timeline_file(filepath):
    timeline = []
    first_line = True
    with open(filepath, 'r') as f:
        while True:
            line = f.readline()
            if line == '':
                break
            if first_line:
                first_line = False
                continue
            parts = line.strip().split(',')

            parts[0] = int(parts[0])
            parts[1:] = map(float, parts[1:])
            timeline.append(parts)
    return timeline

def calculate_one(parent, entropy_filepath):
    if not os.path.isdir(parent):
        return 0
    if "net" in parent:
        env = 'net'
    elif "spb" in parent:
        env = 'spb'
    else:
        print('dir is wrong')
        return 0

    if re.search(r'not$', parent) is not None:
        return 0

    if not os.path.exists(os.path.join(parent, 'k8s-cpu')) and \
        not os.path.exists(os.path.join(parent, 'ts-cpu')):
        print(parent, 'Not found k8s-cpu or ts-cpu')
        return 0
    mac_parent = get_mac_parent(parent)
    print(os.getpid(), '====> entropy', mac_parent)
    
    suffix = hashlib.md5(mac_parent.encode('utf-8')).hexdigest()[:6]
    if env == 'net':
        out_filepath = os.path.join(parent, f"{env}_naue_{time_interval//1000000}_thing_send-{suffix}-6.csv")
    
    elif env == 'spb':
        out_filepath = os.path.join(parent, f"{env}_naue_{time_interval//1000000}_thing_send-{suffix}-5.csv")
        if os.path.exists(out_filepath):
            eff_ne_timeline = calculate_eff_ne_usage(parent, env, time_interval, [])
            if len(eff_ne_timeline) == 0:
                print('!!!! ', parent, "no effective usage !!!!")
                return 0
        
            timeline = read_timeline_file(out_filepath)
            ei, ti = 0, 0
            new_timeline = []
            while ti < len(timeline):
                unit = timeline[ti]
                if timeline[ti][0] > eff_ne_timeline[ei][0]:
                    assert eff_ne_timeline[ei][3] == 0
                    ei += 1
                elif timeline[ti][0] < eff_ne_timeline[ei][0]:
                    new_unit = unit[:EFF_U_ALL_IDX+1]
                    new_unit = new_unit + [0,0,0]
                    new_timeline.append(new_unit)
                    ti += 1
                else:
                    new_unit = unit[:EFF_U_ALL_IDX+1]
                    new_unit = new_unit + eff_ne_timeline[ei][1:4]
                    new_timeline.append(new_unit)
                    ti += 1
                    ei += 1
            out_filepath = os.path.join(parent, f"{env}_naue_{time_interval//1000000}_thing_send-{suffix}-6.csv")
            output_timeline(new_timeline, out_filepath)
        out_filepath = os.path.join(parent, f"{env}_naue_{time_interval//1000000}_thing_send-{suffix}-6.csv")

    if os.path.exists(out_filepath):  # 文件已经存在，直接读取
        timeline = read_timeline_file(out_filepath)
        if len(timeline) == 0:
            print('!!!! ', parent, 'timeline length is zero!!!!')
            return 0

    else:  # 文件不存在，需要计算
        need_timeline = calculate_need(parent, env, time_interval)
        if len(need_timeline) == 0:
            print('!!!! ', parent, 'no need !!!!')
            return 0

        alloc_usage_timeline = calculate_usage_alloc(
            env, parent, time_interval)
        if len(alloc_usage_timeline) == 0:
            print('!!!! ', parent, 'no usage !!!!')
            return 0

        eff_timeline = calculate_eff_usage(parent, env, time_interval)
        if len(eff_timeline) == 0:
            print('!!!! ', parent, "no effective usage !!!!")
            return 0
        
        eff_ne_timeline = calculate_eff_ne_usage(parent, env, time_interval, eff_timeline)
        if len(eff_ne_timeline) == 0:
            print('!!!! ', parent, "no effective usage !!!!")
            return 0

        need_len, au_len, eff_len, eff_ne_len = len(need_timeline), \
                                    len(alloc_usage_timeline), \
                                    len(eff_timeline), len(eff_ne_timeline)
        ts_beg_need, ts_end_need = need_timeline[0][0], need_timeline[need_len-1][0]
        ts_beg_au, ts_end_au = alloc_usage_timeline[0][0], alloc_usage_timeline[au_len-1][0]
        ts_beg_eff, ts_end_eff = eff_timeline[0][0], eff_timeline[eff_len-1][0]
        ts_beg_eff_ne, ts_end_eff_ne = eff_ne_timeline[0][0], eff_ne_timeline[eff_ne_len-1][0]
        
        ts_beg_need %= 1000000
        ts_end_need %= 1000000
        ts_beg_au %= 1000000
        ts_end_au %= 1000000
        ts_beg_eff %= 1000000
        ts_end_eff %= 1000000
        ts_beg_eff_ne %= 1000000
        ts_end_eff_ne %= 1000000

        ts_first = min(ts_beg_need, ts_beg_au, ts_beg_eff, ts_beg_eff_ne)
        ts_last = max(ts_end_need, ts_end_au, ts_end_eff, ts_end_eff_ne)

        i_need = 0
        i_au = 0
        i_eff = 0
        i_eff_ne = 0
        timeline = []
        ts_cur = ts_first
        while ts_cur != ts_last+1:
            record = [0] * 19
            record[0] = ts_cur
            if i_need < need_len and need_timeline[i_need][0] % 1000000 == ts_cur:
                record[1:7] = need_timeline[i_need][1:]
                i_need += 1
            if i_au < au_len and alloc_usage_timeline[i_au][0] % 1000000 == ts_cur:
                record[7:13] = alloc_usage_timeline[i_au][1:]
                i_au += 1
            if i_eff < eff_len and eff_timeline[i_eff][0] % 1000000 == ts_cur:
                record[13:16] = eff_timeline[i_eff][1:]
                i_eff += 1
            if i_eff_ne < eff_ne_len and eff_ne_timeline[i_eff_ne][0] % 1000000 == ts_cur:
                record[16:] = eff_ne_timeline[i_eff_ne][1:]
                i_eff_ne += 1
            timeline.append(record)
            ts_cur = (ts_cur+1) % 1000000
        output_timeline(timeline, out_filepath)

    result = build_str_entropy(timeline, parent)
    # result = build_str_entropy_v5(timeline, parent)
    # result =  build_str_an_ua_eu_with_var(timeline, parent)
    if result is None:
        print('!!!! ', parent, ' str entropy is None !!!!')
        return 0
    
    with lock, open(entropy_filepath, 'a') as f:
        f.write(result+'\n')
    return 0


def extract_meta(parent):
    main_part = parent.split('/')[-1]
    parts = main_part.split('-')
    t_run = parts[0]
    env = parts[1]
    no_task = parts[2]
    config = ''
    acc_speed = ''
    peak_task = ''
    if env == 'net':
        config = parts[-2]
        if len(parts) == 7:
            peak_task = parts[3]
            acc_speed = parts[4]
    else:
        if len(parts) == 5:
            peak_task = parts[3]
            acc_speed = parts[4]
    if acc_speed != '':
        int_acc_speed = int(acc_speed)
        if int_acc_speed == 20:
            acc_speed = '0.2'
        elif int_acc_speed > 20 and int_acc_speed != 50:
            acc_speed = int_acc_speed / 100
    return t_run, env, no_task, config, acc_speed, peak_task


def build_str(timeline, parent):
    t_run, env, no_task, config, acc_speed, peak_task = extract_meta(parent)

    yld = float(get_yield(parent)) / 100
    goodput = get_goodput(parent)
    if yld == -1 or goodput == -1:
        return None

    i_need_beg, i_need_end = find_need_range(timeline, parent)
    un_ratio = get_un(timeline, i_need_beg, i_need_end, env)
    ur_need = get_ur(timeline, i_need_beg, i_need_end)
    acc_need, acc_var_need = get_acc(timeline, i_need_beg, i_need_end)
    uo_need, uo_var_need = get_uo(timeline, i_need_beg, i_need_end)
    i_alloc_beg, i_alloc_end = find_alloc_range(timeline, parent)
    ur_alloc = get_ur(timeline, i_alloc_beg, i_alloc_end)
    acc_alloc, acc_var_alloc = get_acc(timeline, i_alloc_beg, i_alloc_end)
    uo_alloc, uo_var_alloc = get_uo(timeline, i_alloc_beg, i_alloc_end)

    if un_ratio == -1 or uo_alloc == 1 or acc_alloc == -1 or yld == -1:
        return 0
    len_need_range = i_need_end - i_need_beg + 1
    len_alloc_range = i_alloc_end - i_alloc_beg + 1
    return ','.join(map(str, [
        t_run, env, no_task, config, acc_speed, peak_task, 
        un_ratio, 
        uo_alloc, uo_var_alloc, 
        acc_alloc, acc_var_alloc, 
        ur_need, ur_alloc, 
        yld, goodput, 
        i_need_beg, len_need_range, len_alloc_range
    ]))


def build_str_entropy_v5(timeline, parent):
    t_run, env, no_task, config, acc_speed, peak_task = extract_meta(parent)

    yld = float(get_yield(parent)) / 100
    goodput = get_goodput(parent)
    if yld == -1 or goodput == -1:
        return None

    def cal_ratio(need, usage, occupy, eff_u):
        on, uo, eu, en = -1, -1, -1, -1
        if need > 0:
            on = occupy / need
            en = eff_u / need
        if occupy > 0:
            uo = usage / occupy
        if usage > 0:
            eu = eff_u / usage
        return on, uo, eu, en

    i_need_beg, i_need_end = find_need_range(timeline, parent)
    need_need, usage_need, occupy_need, eff_need = get_all_need_usage_occupy_eff(
        timeline, i_need_beg, i_need_end, env)
    on_need, uo_need, eu_need, en_need = cal_ratio(
        need_need, usage_need, occupy_need, eff_need)
    usage_entroy_need, usage_log_S_need = get_usage_entropy(
        timeline, i_need_beg, i_need_end)
    eff_usage_entropy_need, eff_usage_log_S_need = get_eff_usage_entropy(
        timeline, i_need_beg, i_need_end)
    eff_need_entropy_need, eff_need_log_S_need = get_eff_need_entropy(
        timeline, i_need_beg, i_need_end)
    occupy_need_entropy_need, occupy_need_log_S_need = get_occupy_need_entropy(
        timeline, i_need_beg, i_need_end)

    i_alloc_beg, i_alloc_end = find_alloc_range(timeline, parent)
    need_alloc, usage_alloc, occupy_alloc, eff_alloc = get_all_need_usage_occupy_eff(
        timeline, i_alloc_beg, i_alloc_end, env)
    on_alloc, uo_alloc, eu_alloc, en_alloc = cal_ratio(
        need_alloc, usage_alloc, occupy_alloc, eff_alloc)
    usage_entroy_alloc, usage_log_S_alloc = get_usage_entropy(  # 使用分配
        timeline, i_alloc_beg, i_alloc_end)
    eff_usage_entropy_alloc, eff_usage_log_S_alloc = get_eff_usage_entropy(  # 有效使用
        timeline, i_alloc_beg, i_alloc_end)
    eff_need_entropy_alloc, eff_need_log_S_alloc = get_eff_need_entropy(  # 有效需求
        timeline, i_alloc_beg, i_alloc_end)
    occupy_need_entropy_alloc, occupy_need_log_S_alloc = get_occupy_need_entropy( # 分配需求
        timeline, i_alloc_beg, i_alloc_end)

    if on_need + uo_need + eu_need == -3 and on_alloc + uo_alloc + eu_alloc == -3:
        return 0

    len_need_range = i_need_end - i_need_beg + 1
    len_alloc_range = i_alloc_end - i_alloc_beg + 1
    return ','.join(map(str, [
        t_run, env, no_task, config, acc_speed, peak_task,

        on_need, uo_need, eu_need, en_need,
        occupy_need_entropy_need, occupy_need_log_S_need,
        usage_entroy_need, usage_log_S_need,
        eff_usage_entropy_need, eff_usage_log_S_need, 
        eff_need_entropy_need, eff_need_log_S_need,
        
        on_alloc, uo_alloc, eu_alloc, en_alloc,
        occupy_need_entropy_alloc, occupy_need_log_S_alloc,
        usage_entroy_alloc, usage_log_S_alloc,
        eff_usage_entropy_alloc, eff_usage_log_S_alloc,
        eff_need_entropy_alloc, eff_need_log_S_alloc,
        
        yld, goodput,
        i_need_beg, len_need_range, len_alloc_range
    ]))



def build_str_entropy(timeline, parent):
    t_run, env, no_task, config, acc_speed, peak_task = extract_meta(parent)

    yld = float(get_yield(parent)) / 100
    goodput = get_goodput(parent)
    if yld == -1 or goodput == -1:
        return None
    
    yld_mach = -1
    if env == 'spb':
        yld_mach = get_msg_mach_yield(parent)

    def cal_ratio(need, usage, occupy, eff_u, eff_u_ne):
        on, uo, eu, en, eu_ne, en_ne = -1, -1, -1, -1, -1, -1
        if need > 0:
            on = occupy / need
            en = eff_u / need
            en_ne = eff_u_ne / need
        if occupy > 0:
            uo = usage / occupy
        if usage > 0:
            eu = eff_u / usage
            eu_ne = eff_u_ne / usage
        return on, uo, eu, en, en_ne, eu_ne

    # 计算从发起需求到计算结束时间段的熵
    i_comp_beg, i_comp_end = find_comp_range(timeline, parent)
    if i_comp_beg == -1 or i_comp_end == -1:
        print(f'{parent} log not long enough')
        return None
    need_comp, usage_comp, occupy_comp, eff_comp, eff_ne_comp = \
        get_all_need_usage_occupy_eff(timeline, i_comp_beg, i_comp_end, env)
    on_comp, uo_comp, eu_comp, en_comp, en_ne_comp, eu_ne_comp = \
        cal_ratio(need_comp, usage_comp, occupy_comp, eff_comp, eff_ne_comp)
    an_S_comp, an_log_S_comp, \
        ua_S_comp, ua_log_S_comp, \
        eu_S_comp, eu_log_S_comp, \
        en_S_comp, en_log_S_comp, \
        en_ne_S_comp, en_ne_log_S_comp = get_an_ua_eu_en_entropy_v7(timeline, i_comp_beg, i_comp_end, 1, env)
    ave_usage_comp = get_ave_usage(timeline, i_comp_beg, i_comp_end)

    # 计算从发起需求到请求结束时间段的熵
    i_need_beg, i_need_end = find_need_range(timeline, parent)
    need_need, usage_need, occupy_need, eff_need, eff_ne_need = \
        get_all_need_usage_occupy_eff(timeline, i_need_beg, i_need_end, env)
    on_need, uo_need, eu_need, en_need, en_ne_need, eu_ne_need = \
        cal_ratio(need_need, usage_need, occupy_need, eff_need, eff_ne_need)
    an_S_need, an_log_S_need, \
        ua_S_need, ua_log_S_need, \
        eu_S_need, eu_log_S_need, \
        en_S_need, en_log_S_need, \
        en_ne_S_need, en_ne_log_S_need = get_an_ua_eu_en_entropy_v7(timeline, i_need_beg, i_need_end, 1, env)
    ave_usage_need = get_ave_usage(timeline, i_need_beg, i_need_end)

    # 计算从发起请求到分配结束时间段的熵
    i_alloc_beg, i_alloc_end = find_alloc_range(timeline, parent)
    need_alloc, usage_alloc, occupy_alloc, eff_alloc, eff_ne_alloc = \
        get_all_need_usage_occupy_eff(timeline, i_alloc_beg, i_alloc_end, env)
    on_alloc, uo_alloc, eu_alloc, en_alloc, en_ne_alloc, eu_ne_alloc = \
        cal_ratio(need_alloc, usage_alloc, occupy_alloc, eff_alloc, eff_ne_alloc)
    an_S_alloc, an_log_S_alloc, \
        ua_S_alloc, ua_log_S_alloc, \
        eu_S_alloc, eu_log_S_alloc, \
        en_S_alloc, en_log_S_alloc, \
        en_ne_S_alloc, en_ne_log_S_alloc = get_an_ua_eu_en_entropy_v7(timeline, i_alloc_beg, i_alloc_end, 1, env)
    ave_usage_alloc = get_ave_usage(timeline, i_alloc_beg, i_alloc_end)

    if on_need + uo_need + eu_need == -3 and on_alloc + uo_alloc + eu_alloc == -3:
        return None

    with lock:
        comp_ranges = load_comp_ranges(parent)
    task_num = comp_ranges[get_mac_parent(parent)][5]
    if task_num < float(no_task) * 0.625:
        print(parent, "real task is not enough")
        return None

    len_need_range = i_need_end - i_need_beg + 1
    len_alloc_range = i_alloc_end - i_alloc_beg + 1
    len_comp_range = i_comp_end - i_comp_beg + 1
    return ','.join(map(str, [
        t_run, env, no_task, task_num, config, acc_speed, peak_task,

        ave_usage_need, on_need, uo_need, eu_need, en_need, en_ne_need, eu_ne_need,
        an_S_need, an_log_S_need,
        ua_S_need, ua_log_S_need,
        eu_S_need, eu_log_S_need, 
        en_S_need, en_log_S_need,
        en_ne_S_need, en_ne_log_S_need,
        
        ave_usage_alloc, on_alloc, uo_alloc, eu_alloc, en_alloc, en_ne_alloc, eu_ne_alloc,
        an_S_alloc, an_log_S_alloc, 
        ua_S_alloc, ua_log_S_alloc, 
        eu_S_alloc, eu_log_S_alloc, 
        en_S_alloc, en_log_S_alloc,
        en_ne_S_alloc, en_ne_log_S_alloc,
        
        ave_usage_comp, on_comp, uo_comp, eu_comp, en_comp, en_ne_comp, eu_ne_comp,
        an_S_comp, an_log_S_comp,
        ua_S_comp, ua_log_S_comp,
        eu_S_comp, eu_log_S_comp, 
        en_S_comp, en_log_S_comp,
        en_ne_S_comp, en_ne_log_S_comp,
        
        yld, yld_mach, goodput,
        i_need_beg, len_need_range, len_alloc_range, len_comp_range
    ]))


def build_str_an_ua_eu_with_var(timeline, parent):
    t_run, env, no_task, config, acc_speed, peak_task = extract_meta(parent)

    yld = float(get_yield(parent)) / 100
    goodput = get_goodput(parent)
    if yld == -1 or goodput == -1:
        return None

    span = 10
    i_need_beg, i_need_end = find_need_range(timeline, parent)
    an_need, an_var_need, ua_need, ua_var_need, eu_need, eu_var_need = get_an_ua_eu_with_var(timeline, i_need_beg, i_need_end, span)
    if an_need == -1:
        return None

    i_alloc_beg, i_alloc_end = find_alloc_range(timeline, parent)
    an_alloc, an_var_alloc, ua_alloc, ua_var_alloc, eu_alloc, eu_var_alloc = get_an_ua_eu_with_var(timeline, i_alloc_beg, i_alloc_end, span)
    if an_alloc == -1:
        return None
    
    return ','.join(map(str, [
        t_run, env, no_task, config, acc_speed, peak_task,

        an_need, an_var_need,
        ua_need, ua_var_need,
        eu_need, eu_var_need,

        an_alloc, an_var_alloc,
        ua_alloc, ua_var_alloc,
        eu_alloc, eu_var_alloc,
        
        yld, goodput,
        i_need_beg, i_need_end-i_need_beg+1, i_alloc_end-i_alloc_beg+1
    ]))


NEED_FAST_ALL_IDX = 3
NEED_SLOW_ALL_IDX = 6
ALLOC_ALL_IDX = 9
USAGE_ALL_IDX = 12
EFF_U_ALL_IDX = 15
EFF_U_NE_ALL_IDX = 18


def find_need_range(timeline, parent):
    ts_first_thing_send, ts_last_thing_send, ts_last_comp, ts_analysis = get_time_range(parent)
    
    s_beg_time = (ts_first_thing_send//time_interval)%1000000
    s_end_time = (ts_last_thing_send//time_interval)%1000000
    
    i_beg = 0
    while timeline[i_beg][0] != s_beg_time:
        i_beg += 1
    while i_beg-1 >= 0 and timeline[i_beg-1][NEED_FAST_ALL_IDX] != 0:
        i_beg -= 1
    while timeline[i_beg][NEED_FAST_ALL_IDX] == 0:
        i_beg += 1

    i_end = i_beg
    while i_end < len(timeline) and timeline[i_end][0] != s_end_time:
        i_end += 1
    if i_end == len(timeline):
        i_end -= 1
    while i_end+1 < len(timeline) and timeline[i_end+1][NEED_FAST_ALL_IDX] != 0:
        i_end += 1
    while timeline[i_end][NEED_FAST_ALL_IDX] == 0:
        i_end -= 1

    return i_beg, i_end


def find_alloc_range(timeline, parent):
    env = 'net' if 'net' in parent else 'spb'
    if env == 'net':
        request, limit = get_k8s_req_lim(parent)

    i_need_beg, i_need_end = find_need_range(timeline, parent)
    i_beg = i_need_beg
    i_end = i_need_end
    i_cur = i_end
    no_stop = 0
    while i_cur < len(timeline):
        unit = timeline[i_cur]
        alloc_bj = unit[ALLOC_ALL_IDX - 2]
        alloc_nj = unit[ALLOC_ALL_IDX - 1]
        alloc_all = unit[ALLOC_ALL_IDX]
        usage_all = unit[USAGE_ALL_IDX]
        if (re.search('-1$', parent) is not None and env == 'net' and alloc_bj <= request and alloc_nj <= request) or \
           (env == 'spb' and alloc_all == 0) or \
           (re.search('-2$', parent) is not None and env == 'net' and usage_all <= alloc_all/2.):
            no_stop += 1
            if no_stop == 50:
                break
            i_cur += 1
            continue
        no_stop = 0
        i_end = i_cur
        i_cur += 1
    return i_beg, i_end


def load_comp_ranges(parent):
    if os.path.exists(os.path.join(parent, '../comp_ranges.json')):
        with open(os.path.join(parent, '../comp_ranges.json'), 'r') as f:
            return json.load(f)
    return {}

def dump_comp_ranges(parent, data):
    with open(os.path.join(parent, '../comp_ranges.json'), 'w') as f:
        json.dump(data, f, indent=2)

def load_log_time_range(dir):
    time_ranges = dict()
    filenames = os.listdir(dir)
    for filename in filenames:
        name, ext = os.path.splitext(filename)
        if name.find("log") != -1 or ext != ".txt":
            continue

        with open(os.path.join(dir, filename), "r") as f:
            while True:
                line = f.readline().strip()
                if line is None or line == "":
                    break

                items = line.split(",")
                if len(items) < 4:
                    continue

                if '.' in items[4]:
                    msg_id = msg_id_dot2int(items[4])
                else:
                    msg_id = int(items[4])
                if get_location(msg_id) > 2 or get_location(msg_id) == 0:
                    continue
                
                time = int(items[3])
                if time == -6795364578871345152:
                    continue
                assert time > 1600000000000000000, f'{dir}, {filename}, {items}'
                
                if msg_id not in time_ranges:
                    time_ranges[msg_id] = [time, time]
                else:
                    time_range = time_ranges[msg_id]
                    if time < time_range[0]:
                        time_range[0] = time
                    elif time > time_range[1]:
                        time_range[1] = time
    return time_ranges

def get_time_range(parent):
    with lock:
        comp_ranges = load_comp_ranges(parent)
    mac_parent = get_mac_parent(parent)
    if mac_parent in comp_ranges and len(comp_ranges[mac_parent]) == 6:
        ts_first_thing_send, ts_last_thing_send, ts_last_comp, ts_analysis, _, _ = comp_ranges[mac_parent]
        return ts_first_thing_send, ts_last_thing_send, ts_last_comp, ts_analysis
    
    log_dirpath = None
    for file in os.listdir(parent):
        if not os.path.isdir(os.path.join(parent, file)):
            continue
        if file.startswith('2022'):
            log_dirpath = os.path.join(parent, file)
            break
    if log_dirpath is None:
        print(parent, 'Not found log dirpath')
        return []
    msg_time_ranges = load_log_time_range(log_dirpath)

    task_num = 0
    ts_first_thing_send = -1
    ts_last_thing_send = -1
    ts_analysis = -1
    ts_last_comp = -1
    for msg_id, time_range in msg_time_ranges.items():
        if get_location(msg_id) > 2:  # invalid message id
            continue
        if check_noise(msg_id) or check_warm(msg_id):
            continue
        if check_person(msg_id):
            ts_analysis = time_range[0]
            continue
        
        task_num += 1
        if ts_first_thing_send == -1 or time_range[0] < ts_first_thing_send:
            ts_first_thing_send = time_range[0]
        if ts_last_thing_send == -1 or time_range[0] > ts_last_thing_send:
            ts_last_thing_send = time_range[0]
        if ts_last_comp == -1 or time_range[1] > ts_last_comp:
            ts_last_comp = time_range[1]
    
    with lock:
        comp_ranges = load_comp_ranges(parent)
        comp_ranges[mac_parent] = (ts_first_thing_send, ts_last_thing_send, 
                                   ts_last_comp, ts_analysis, ts_last_comp < ts_analysis,
                                   task_num)
        dump_comp_ranges(parent, comp_ranges)
    return ts_first_thing_send, ts_last_thing_send, ts_last_comp, ts_analysis


def find_comp_range(timeline, parent):
    ts_first_thing_send, ts_last_thing_send, ts_last_comp, ts_analysis = get_time_range(parent)
    
    s_beg_time = (ts_first_thing_send//time_interval)%1000000
    s_end_time = (ts_last_comp//time_interval)%1000000
    
    i_beg = 0
    while timeline[i_beg][0] != s_beg_time:
        i_beg += 1
        
    i_end = i_beg
    while i_end < len(timeline) and timeline[i_end][0] != s_end_time:
        i_end += 1
    
    if i_end == len(timeline):
        i_end -= 1
        print(parent, ' computing out of the monitoring range')
    if ts_analysis < ts_last_comp:
        print(parent, ' analysis time before the last log time')
    return i_beg, i_end


def get_all_need_usage_occupy_eff(timeline, i_beg, i_end, env='net'):
    if i_beg < 0:
        return -1, -1, -1, -1, -1

    need_fast_total = 0
    usage_total = 0
    occupy_total = 0
    eff_u_total = 0
    eff_u_ne_total = 0
    for idx_unit in range(i_beg, i_end + 1):
        unit = timeline[idx_unit]
        need_fast_all = unit[NEED_FAST_ALL_IDX]
        alloc_all = unit[ALLOC_ALL_IDX]
        # usage_all = unit[USAGE_ALL_IDX] if env == 'net' else unit[ALLOC_ALL_IDX]
        usage_all = unit[USAGE_ALL_IDX]
        occupy_all = max(alloc_all, usage_all)
        eff_u_all = unit[EFF_U_ALL_IDX]
        eff_u_ne_all = unit[EFF_U_NE_ALL_IDX]

        need_fast_total += need_fast_all
        usage_total += usage_all
        occupy_total += occupy_all
        eff_u_total += eff_u_all
        eff_u_ne_total += eff_u_ne_all
    return need_fast_total, usage_total, occupy_total, eff_u_total, eff_u_ne_total


def get_usage_entropy(timeline, i_beg, i_end, env='net'):
    if i_beg < 0:
        return -1, -1

    freq = {}
    total = 0
    for idx_unit in range(i_beg, i_end + 1):
        unit = timeline[idx_unit]
        alloc_all = unit[ALLOC_ALL_IDX]
        # usage_all = unit[USAGE_ALL_IDX] if env == 'net' else unit[ALLOC_ALL_IDX]
        usage_all = unit[USAGE_ALL_IDX]
        occupy_all = max(alloc_all, usage_all)

        if occupy_all == 0:
            ratio = 100
        else:
            ratio = int(usage_all / occupy_all * 100 + 0.5)
        if ratio not in freq:
            freq[ratio] = 1
        else:
            freq[ratio] += 1
        total += 1

    entropy = 0
    log_entropy = 0
    for ratio, count in freq.items():
        ratio /= 100.
        p = count / total
        log_entropy += -1 * p * math.log2(p)
        if ratio == 1:
            continue
        p = count / total
        # pu = p * ((1 - ratio/100)**4) / 4
        pu = p * ((1-ratio)/4/(1+ratio))**2
        assert (pu <= 0.5)
        entropy += -16 * pu * math.log2(pu)
    return entropy, log_entropy


def get_eff_usage_entropy(timeline, i_beg, i_end, env='net'):
    if i_beg < 0:
        return -1, -1

    freq = {}
    total = 0
    for idx_unit in range(i_beg, i_end + 1):
        unit = timeline[idx_unit]
        # usage_all = unit[USAGE_ALL_IDX] if env == 'net' else unit[ALLOC_ALL_IDX]
        usage_all = unit[USAGE_ALL_IDX]
        eff_u_all = unit[EFF_U_ALL_IDX]

        if usage_all == 0:
            ratio = 100
        else:
            ratio = min(100, int(eff_u_all / usage_all * 100 + 0.5)) # TODO 存在有效使用大于使用的情况
        if ratio not in freq:
            freq[ratio] = 1
        else:
            freq[ratio] += 1
        total += 1

    entropy = 0
    log_entropy = 0
    for ratio, count in freq.items():
        ratio /= 100.
        p = count / total
        log_entropy += -1 * p * math.log2(p)
        if ratio == 1:
            continue
        # pu = p * ((1-ratio/100)**4)/4
        pu = p * ((1-ratio)/4/(1+ratio))**2
        assert (pu <= 0.5)
        entropy += -16 * pu * math.log2(pu)
    return entropy, log_entropy


def get_eff_need_entropy(timeline, i_beg, i_end, env='net'):
    if i_beg < 0:
        return -1, -1

    freq = {}
    total = 0
    for idx_unit in range(i_beg, i_end + 1):
        unit = timeline[idx_unit]
        need_fast_all = unit[NEED_FAST_ALL_IDX]
        # usage_all = unit[USAGE_ALL_IDX] if env == 'net' else unit[ALLOC_ALL_IDX]
        eff_u_all = unit[EFF_U_ALL_IDX]

        if need_fast_all == 0:
            ratio = 100
        else:
            ratio = min(100, int(eff_u_all / need_fast_all * 100 + 0.5)) # TODO 存在有效使用大于需求的情况
        if ratio not in freq:
            freq[ratio] = 1
        else:
            freq[ratio] += 1
        total += 1

    entropy = 0
    log_entropy = 0
    for ratio, count in freq.items():
        ratio /= 100.
        p = count / total
        log_entropy += -1 * p * math.log2(p)
        if ratio == 1:
            continue
        p = count / total
        # pu = p * ((1-ratio/100)**4)/4
        pu = p * ((1-ratio)/4/(1+ratio))**2
        assert (pu <= 0.5)
        entropy += -16 * pu * math.log2(pu)
    return entropy, log_entropy


def get_occupy_need_entropy(timeline, i_beg, i_end, env='net'):
    if i_beg < 0:
        return -1, -1

    freq = {}
    total = 0
    for idx_unit in range(i_beg, i_end + 1):
        unit = timeline[idx_unit]
        need_fast_all = unit[NEED_FAST_ALL_IDX]
        alloc_all = unit[ALLOC_ALL_IDX]
        usage_all = unit[USAGE_ALL_IDX]
        occupy_all = max(alloc_all, usage_all)

        if need_fast_all == 0:
            ratio = 999999999999999999999999999
        else:
            ratio = int(occupy_all / need_fast_all * 100 + 0.5)
        # if need_fast_all + occupy_all == 0:
        #     ratio = 100
        # else:
        #     # tmp = ((occupy_all-need_fast_all)/(need_fast_all+occupy_all))**2
        #     ratio = min(100, int(tmp * 100 + 0.5))
        if ratio not in freq:
            freq[ratio] = 1
        else:
            freq[ratio] += 1
        total += 1

    entropy = 0
    log_entropy = 0
    for ratio, count in freq.items():
        ratio /= 100.
        p = count / total
        log_entropy += -1 * p * math.log2(p)
        if ratio == 1:
            continue
        # pu = p * ((ratio/100)**4)/4
        pu = p * ((1-ratio)/4/(1+ratio))**2
        assert (pu <= 0.5)
        entropy += -16 * pu * math.log2(pu)
    return entropy, log_entropy

# f(ui) = (((1-qi*ui)/(1+qi*ui))**2) / 16
def get_an_ua_eu_en_entropy_v6(timeline, i_beg, i_end, span=1):
    if i_beg < 0:
        return -1, -1, -1, -1, -1, -1, -1, -1

    an_items = {}
    ua_items = {}
    eu_items = {}
    en_items = {}

    def add_dict(items, item):
        if item not in items:
            items[item] = 1
        else:
            items[item] += 1

    i_cur = i_beg
    while i_cur <= i_end:
        cnt = 0
        need_item = 0
        usage_item = 0
        alloc_item = 0
        eff_item = 0
        while i_cur <= i_end and cnt < span:
            unit = timeline[i_cur]
            need_all = unit[NEED_FAST_ALL_IDX]
            need_item += need_all

            usage_all = unit[USAGE_ALL_IDX]
            usage_item += usage_all

            quota_all = unit[ALLOC_ALL_IDX]
            alloc_all = max(usage_all, quota_all)
            alloc_item += alloc_all

            eff_all = unit[EFF_U_ALL_IDX]
            eff_item += eff_all
            
            i_cur += 1
            cnt += 1
        
        an_ratio = int(alloc_item/need_item * 100 + 0.5) if need_item > 0 else 999999999999999999999999999
        add_dict(an_items, an_ratio/100.)
        
        ua_ratio = min(100, int(usage_item/alloc_item * 100 + 0.5)) if alloc_item > 0 else 100
        add_dict(ua_items, ua_ratio/100.)
        
        eu_ratio = min(100, int(eff_item/usage_item * 100 + 0.5)) if usage_item > 0 else 100
        add_dict(eu_items, eu_ratio/100.)
        
        en_ratio = min(100, int(eff_item/need_item * 100 + 0.5)) if need_item > 0 else 100
        add_dict(en_items, en_ratio/100.)
    
    def cal_entropy(items: dict):
        total = 0
        for cnt in items.values():
            total += cnt

        qi_deno = 0
        for um, cnt_m in items.items():
            pm = cnt_m / total
            for un, cnt_n in items.items():
                pn = cnt_n / total
                qi_deno += pm * pn * (um - un)**2

        entropy, log_entropy = 0, 0
        for ui, cnt_i in items.items():
            pi = cnt_i / total
            log_entropy += -1 * pi * math.log2(pi)

            if ui == 1:
                continue

            qi_nume = 0
            for un, cnt_n in items.items():
                pn = cnt_n / total
                qi_nume += pi * pn * (ui - un)**2
            qi = qi_nume / qi_deno if qi_deno > 0 else 1

            fi = (((1-qi*ui)/(1+qi*ui))**2)/16
            pi_fi = pi * fi

            entropy += -pi_fi * math.log2(pi_fi)
        return entropy, log_entropy

    an_S, an_log_S = cal_entropy(an_items)
    ua_S, ua_log_S = cal_entropy(ua_items)
    eu_S, eu_log_S = cal_entropy(eu_items)
    en_S, en_log_S = cal_entropy(en_items)

    return an_S, an_log_S, ua_S, ua_log_S, eu_S, eu_log_S, en_S, en_log_S


# AN:    f(ui, ai) = (((1-ui)/(1+ui))**2) * ((2*ai+1)/(ai+1)) / 8
# UA,EU: f(ui, ai) = (((1-ui)/(1+ui))**2) * ((2*ai+1)/(ai+1)) / 8
def get_an_ua_eu_en_entropy_v7(timeline, i_beg, i_end, span=1, env='net'):
    if i_beg < 0:
        return -1, -1, -1, -1, -1, -1, -1, -1, -1, -1

    an_items = {}
    ua_items = {}
    eu_items = {}
    en_items = {}
    eu_ne_items = {}
    en_ne_items = {}

    def add_dict(items, item):
        if item not in items:
            items[item] = 1
        else:
            items[item] += 1

    i_cur = i_beg
    while i_cur <= i_end:
        cnt = 0
        need_item = 0
        usage_item = 0
        alloc_item = 0
        eff_item = 0
        eff_ne_item = 0
        while i_cur <= i_end and cnt < span:
            unit = timeline[i_cur]
            need_all = unit[NEED_FAST_ALL_IDX]
            need_item += need_all

            usage_all = unit[USAGE_ALL_IDX]
            usage_item += usage_all

            quota_all = unit[ALLOC_ALL_IDX]
            alloc_all = max(usage_all, quota_all)
            alloc_item += alloc_all

            eff_all = unit[EFF_U_ALL_IDX]
            eff_item += eff_all
            
            eff_ne_all = unit[EFF_U_NE_ALL_IDX]
            eff_ne_item += eff_ne_all

            i_cur += 1
            cnt += 1
        
        an_ratio = int(alloc_item/need_item * 100 + 0.5) if need_item > 0 else 999999999999999999999999999
        add_dict(an_items, an_ratio/100.)
        
        ua_ratio = min(100, int(usage_item/alloc_item * 100 + 0.5)) if alloc_item > 0 else 100
        add_dict(ua_items, ua_ratio/100.)
        
        eu_ratio = min(100, int(eff_item/usage_item * 100 + 0.5)) if usage_item > 0 else 100
        add_dict(eu_items, eu_ratio/100.)
        
        en_ratio = min(100, int(eff_item/need_item * 100 + 0.5)) if need_item > 0 else 100
        add_dict(en_items, en_ratio/100.)
        
        eu_ne_ratio = min(100, int(eff_ne_item/usage_item * 100 + 0.5)) if usage_item > 0 else 100
        add_dict(eu_ne_items, eu_ne_ratio/100.)
        
        en_ne_ratio = min(100, int(eff_ne_item/need_item * 100 + 0.5)) if need_item > 0 else 100
        add_dict(en_ne_items, en_ne_ratio/100.)
    
    def cal_ai(items:dict, total, ui):
        ai = 0
        exist_same = False
        for un, cnt_n in items.items():
            if ui == un:
                exist_same = True
                continue
            pn = cnt_n / total
            ai += pn * abs(ui - un)
        assert (exist_same == True)
        return ai

    def cal_entropy_an(items: dict):
        total = 0
        for cnt in items.values():
            total += cnt

        entropy, log_entropy = 0, 0
        for ui, cnt_i in items.items():
            pi = cnt_i / total
            log_entropy += -1 * pi * math.log2(pi)

            if ui == 1:
                continue
            
            ai = cal_ai(items, total, ui)
            fi = (((1-ui)/(1+ui))**2) * ((2*ai+1)/(ai+1)) / 8
            qi = pi * fi
            entropy += -qi * math.log2(qi)
        return 4 * entropy, log_entropy

    def cal_entropy_ua_eu(items: dict):
        total = 0
        for cnt in items.values():
            total += cnt

        entropy, log_entropy = 0, 0
        for ui, cnt_i in items.items():
            pi = cnt_i / total
            log_entropy += -1 * pi * math.log2(pi)

            if ui == 1:
                continue

            ai = cal_ai(items, total, ui)
            fi = (1+ai-ui) / 8
            qi = pi * fi
            entropy += -qi * math.log2(qi)
        return 4 * entropy, log_entropy

    an_S, an_log_S = cal_entropy_an(an_items)
    ua_S, ua_log_S = cal_entropy_ua_eu(ua_items)
    eu_S, eu_log_S = cal_entropy_ua_eu(eu_items)
    # en_S, en_log_S = cal_entropy(en_items)
    eu_ne_S, eu_ne_log_S = cal_entropy_ua_eu(eu_ne_items)

    return an_S, an_log_S, ua_S, ua_log_S, eu_S, eu_log_S, 999, 999, eu_ne_S, eu_ne_log_S


def get_un(timeline, i_beg, i_end, env='net'):
    if i_beg < 0:
        return -1

    need_fast_total = 0
    usage_total = 0
    for idx_unit in range(i_beg, i_end + 1):
        unit = timeline[idx_unit]
        need_fast_all = unit[NEED_FAST_ALL_IDX]
        alloc_all = unit[ALLOC_ALL_IDX]
        usage_all = unit[USAGE_ALL_IDX]
        need_fast_total += need_fast_all
        usage_total += usage_all if env == 'net' else alloc_all
    un_ratio = usage_total / need_fast_total if need_fast_total > 0 else -1
    return un_ratio


def get_ur(timeline, i_beg, i_end, env='net'):
    if i_beg < 0:
        return -1

    usage_total = 0
    alloc_total = 0
    for idx_unit in range(i_beg, i_end + 1):
        unit = timeline[idx_unit]
        alloc_all = unit[ALLOC_ALL_IDX]
        usage_all = unit[USAGE_ALL_IDX]
        usage_total += usage_all
        alloc_total += max(usage_all, alloc_all)
    ur_ratio = usage_total / alloc_total
    return ur_ratio


def get_acc(timeline, i_beg, i_end):
    if i_beg < 0:
        return -1, -1

    accs = []
    for idx_unit in range(i_beg, i_end + 1):
        unit = timeline[idx_unit]
        alloc_all = unit[ALLOC_ALL_IDX]
        usage_all = unit[USAGE_ALL_IDX]
        if alloc_all == 0 and usage_all == 0:
            continue
        acc = usage_all / alloc_all if usage_all < alloc_all else alloc_all / usage_all
        accs.append(acc)
    var = np.std(accs)
    ave = np.mean(accs)
    return ave, var


def get_uo(timeline, i_beg, i_end):
    if i_beg < 0:
        return -1, -1

    accs = []
    for idx_unit in range(i_beg, i_end + 1):
        unit = timeline[idx_unit]
        alloc_all = unit[ALLOC_ALL_IDX]
        usage_all = unit[USAGE_ALL_IDX]
        if alloc_all == 0 and usage_all == 0:
            continue
        acc = usage_all / max(usage_all, alloc_all)
        accs.append(acc)
    var = np.std(accs)
    ave = np.mean(accs)
    return ave, var


def get_an_ua_eu_with_var(timeline, i_beg, i_end, span):
    if i_beg < 0:
        return -1, -1, -1, -1, -1, -1

    an_items = []
    ua_items = []
    eu_items = []

    i_cur = i_beg
    while i_cur <= i_end:
        cnt = 0
        need_item = 0
        usage_item = 0
        alloc_item = 0
        eff_item = 0
        while i_cur <= i_end and cnt < span:
            unit = timeline[i_cur]
            need_all = unit[NEED_FAST_ALL_IDX]
            need_item += need_all

            usage_all = unit[USAGE_ALL_IDX]
            usage_item += usage_all

            quota_all = unit[ALLOC_ALL_IDX]
            alloc_all = max(usage_all, quota_all)
            alloc_item += alloc_all

            eff_all = unit[EFF_U_ALL_IDX]
            eff_item += eff_all
            
            i_cur += 1
            cnt += 1
        
        if need_item > 0:
            an_items.append(alloc_item / need_item)
        else:
            an_items.append(-9999999999999)
        
        if alloc_item > 0:
            ua_items.append(usage_item / alloc_item)
        else:
            ua_items.append(-9999999999999)
        
        if usage_item > 0:
            eu_items.append(eff_item / usage_item)
        else:
            eu_items.append(-9999999999999)
    an, an_var = np.mean(an_items), np.std(an_items)
    ua, ua_var = np.mean(ua_items), np.std(ua_items)
    eu, eu_var = np.mean(eu_items), np.std(eu_items)
    return an, an_var, ua, ua_var, eu, eu_var


def calculate_wrapper(parent, out_filepath):
    try:
        log_dirpath = None
        for file in os.listdir(parent):
            if not os.path.isdir(os.path.join(parent, file)):
                continue
            if file.startswith('2022'):
                log_dirpath = os.path.join(parent, file)
                break
        if log_dirpath is None:
            print(parent, 'Not found log dirpath')
            return 0
        if not os.path.exists(os.path.join(log_dirpath, 'spb.jpg')) and \
            not os.path.exists(os.path.join(log_dirpath, 'net.jpg')):
                return 0
        return calculate_one(parent, out_filepath)
    except Exception as e:
        print('!!!! error: ', parent, e)
        return 0

def get_ave_usage(timeline, i_beg, i_end):
    usage_total = 0
    for i_cur in range(i_beg, i_end+1):
        usage_total += timeline[i_cur][12]
    return usage_total / (i_end-i_beg+1)

if __name__ == "__main__":
    grandParent = sys.argv[1]

    suffix = hashlib.md5(grandParent.encode('utf-8')).hexdigest()[:6]
    out_filepath = os.path.join(
        grandParent, f'an_ua_eu_en_entropy_v7-{suffix}.csv')
    entropy_file = open(out_filepath, 'w+')
    # entropy_file.write(','.join([
    #     't_run', 'env', 'no_task', 'real_no_task', 'config', 'acc_speed', 'peak_task',

    #     '平均使用核数_need', '占用/需求_need', '使用/占用_need', '有效/使用_need', '有效/需求_need',
    #     '占用需求熵_need', '占用需求熵_p_need',
    #     '使用率熵_need', '使用率熵_p_need',
    #     '有效使用熵_need', '有效使用熵_p_need',
    #     '有效需求熵_need', '有效需求熵_p_need',
        
    #     '平均使用核数_alloc', '占用/需求_alloc', '使用/占用_alloc', '有效/使用_alloc', '有效/需求_alloc',
    #     '占用需求熵_alloc', '占用需求熵_p_alloc',
    #     '使用率熵_alloc', '使用率熵_p_alloc',
    #     '有效使用熵_alloc', '有效使用熵_p_alloc',
    #     '有效需求熵_alloc', '有效需求熵_p_alloc',
        
    #     '平均使用核数_comp', '占用/需求_comp', '使用/占用_comp', '有效/使用_comp', '有效/需求_comp',
    #     '占用需求熵_comp', '占用需求熵_p_comp',
    #     '使用率熵_comp', '使用率熵_p_comp',
    #     '有效使用熵_comp', '有效使用熵_p_comp',
    #     '有效需求熵_comp', '有效需求熵_p_comp',

    #     'yield', 'yield_mach', 'goodput',
    #     'need_beg', 'need_len', 'alloc_len', 'comp_len'
    # ])+'\n')
    entropy_file.close()
    
    parents = []
    for parent in os.listdir(grandParent):
        path = os.path.join(grandParent, parent)
        if not os.path.isdir(path):
            continue
        if "not" in parent:
            continue
        parents.append(path)
        
    p = Pool(8)
    res_li = []
    parents.sort()
    # parents.reverse()
    for parent in parents:
        res = p.apply_async(calculate_wrapper, (parent, out_filepath))
        res_li.append(res)
    
    for res in res_li:
        r = res.get()
        if r == 0:
            continue
        print(r)
