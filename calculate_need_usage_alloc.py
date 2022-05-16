import hashlib
from json import tool
import math
from multiprocessing import Pool
import sys
import os
import re
import numpy as np

from calculate_need import calculate_need
from src.k8s_cpu_utilization import list_total_cpu, compress_final_data
from calculate_eff_usage import calculate_eff_usage

time_interval = 100 * 1000 * 1000


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
    f.write('ts,need_fast_bj,need_fast_nj,need_fast_all,need_slow_bj,need_slow_nj,need_slow_all,alloc_bj,alloc_nj,alloc_all,usage_bj,usage_nj,usage_all,ratio\n')
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

    if re.search(r'not$', parent) is not None:
        return 0

    if not os.path.exists(os.path.join(parent, 'k8s-cpu')) and not os.path.exists(os.path.join(parent, 'ts-cpu')):
        print('Not found k8s-cpu or ts-cpu')
        return 0
    print(parent)
    suffix = hashlib.md5(parent.encode('utf-8')).hexdigest()[:6]
    out_filepath = os.path.join(
        parent, f"{env}_naue_{time_interval//1000000}_thing_send-{suffix}.csv")
    # if not os.path.exists(out_filepath):
    #     out_filepath = os.path.join(parent, f"{env}_naue_{time_interval//1000000}_thing_send.csv")
    if os.path.exists(out_filepath):  # 文件已经存在，直接读取
        print(f'{out_filepath} already exists')
        timeline = []
        first_line = True
        with open(out_filepath, 'r') as f:
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

    else:  # 文件不存在，需要计算
        need_timeline = calculate_need(parent, env, time_interval)
        if len(need_timeline) == 0:
            return 0

        alloc_usage_timeline = calculate_usage_alloc(
            env, parent, time_interval)
        if len(alloc_usage_timeline) == 0:
            return 0

        eff_timeline = calculate_eff_usage(parent, env, time_interval)
        if len(eff_timeline) == 0:
            print("No effective usage?")
            return 0

        i_need = 0
        i_au = 0
        i_eff = 0
        timeline = []
        while i_need < len(need_timeline) or i_au < len(alloc_usage_timeline) or i_eff < len(eff_timeline):
            record = [0] * 16

            need_unit = need_timeline[i_need] if i_need < len(
                need_timeline) else [0] * len(need_timeline[0])
            au_unit = alloc_usage_timeline[i_au] if i_au < len(alloc_usage_timeline) else [
                0] * len(alloc_usage_timeline[0])
            eff_unit = eff_timeline[i_eff] if i_eff < len(
                eff_timeline) else [0] * len(eff_timeline[0])

            ts_need = need_unit[0] % 1000000 if need_unit[0] != 0 else 1000000
            ts_au = au_unit[0] % 1000000 if au_unit[0] != 0 else 1000000
            ts_eff = eff_unit[0] % 1000000 if eff_unit[0] != 0 else 1000000
            if ts_need <= ts_au and ts_need <= ts_eff:
                record[0] = ts_need
                record[1:7] = need_timeline[i_need][1:]
                i_need += 1
            if ts_au <= ts_need and ts_au <= ts_eff:
                record[0] = ts_au
                record[7:13] = alloc_usage_timeline[i_au][1:]
                i_au += 1
            if ts_eff <= ts_need and ts_eff <= ts_au:
                record[0] = ts_eff
                record[13:] = eff_timeline[i_eff][1:]
                i_eff += 1
            timeline.append(record)
        out_filepath = os.path.join(
            parent, f"{env}_naue_{time_interval//1000000}_thing_send-{suffix}.csv")
        output_timeline(timeline, out_filepath)

    # result = build_str_entropy(timeline, parent)
    result = build_str_entropy_v6(timeline, parent)
    # result =  build_str_an_ua_eu_with_var(timeline, parent)
    if result is None:
        return 0
    return result


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


def build_str_entropy(timeline, parent):
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


# f(ui) = (((1-qi*ui)/(1+qi*ui))**2) / 16
def build_str_entropy_v6(timeline, parent):
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
    an_S_need, an_log_S_need, ua_S_need, ua_log_S_need, eu_S_need, eu_log_S_need, en_S_need, en_log_S_need = get_an_ua_eu_en_entropy(
        timeline, i_need_beg, i_need_end, 1)

    i_alloc_beg, i_alloc_end = find_alloc_range(timeline, parent)
    need_alloc, usage_alloc, occupy_alloc, eff_alloc = get_all_need_usage_occupy_eff(
        timeline, i_alloc_beg, i_alloc_end, env)
    on_alloc, uo_alloc, eu_alloc, en_alloc = cal_ratio(
        need_alloc, usage_alloc, occupy_alloc, eff_alloc)
    an_S_alloc, an_log_S_alloc, ua_S_alloc, ua_log_S_alloc, eu_S_alloc, eu_log_S_alloc, en_S_alloc, en_log_S_alloc = get_an_ua_eu_en_entropy(
        timeline, i_need_beg, i_need_end, 1)

    if on_need + uo_need + eu_need == -3 and on_alloc + uo_alloc + eu_alloc == -3:
        return 0

    len_need_range = i_need_end - i_need_beg + 1
    len_alloc_range = i_alloc_end - i_alloc_beg + 1
    return ','.join(map(str, [
        t_run, env, no_task, config, acc_speed, peak_task,

        on_need, uo_need, eu_need, en_need,
        an_S_need, an_log_S_need,
        ua_S_need, ua_log_S_need,
        eu_S_need, eu_log_S_need, 
        en_S_need, en_log_S_need,
        
        on_alloc, uo_alloc, eu_alloc, en_alloc,
        an_S_alloc, an_log_S_alloc, 
        ua_S_alloc, ua_log_S_alloc, 
        eu_S_alloc, eu_log_S_alloc, 
        en_S_alloc, en_log_S_alloc,
        
        yld, goodput,
        i_need_beg, len_need_range, len_alloc_range
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


def find_need_range(timeline, parent):
    len_timeline = len(timeline)
    if 'net' in parent:
        i_beg = 300
        while timeline[i_beg][NEED_FAST_ALL_IDX] != 0:
            i_beg -= 1
        i_end = 2000
        while i_end < len_timeline and timeline[i_end][NEED_FAST_ALL_IDX] != 0:
            i_end += 1
    else:
        i_beg = 100
        while timeline[i_beg][NEED_FAST_ALL_IDX] != 0:
            i_beg -= 1
        while i_beg+1 < len_timeline and timeline[i_beg+1][ALLOC_ALL_IDX] == 0 and \
                i_beg+2 < len_timeline and timeline[i_beg+2][ALLOC_ALL_IDX] == 0:
            i_beg += 1
        # 寻找范围末尾，认为需求量连续10个0，即为末尾
        i_end = min(i_beg + 400, len_timeline)
        while i_end < len_timeline:
            if timeline[i_end][NEED_FAST_ALL_IDX] != 0:
                i_end += 1
                continue
            all_zero = True
            i_tmp = i_end
            while i_tmp < len_timeline and i_tmp - i_end + 1 <= 10:
                if timeline[i_tmp][NEED_FAST_ALL_IDX] != 0:
                    all_zero = False
                    break
                i_tmp += 1
            if all_zero:
                break
            i_end += 1

    i_need_beg = -1
    i_need_end = -1
    i = i_beg
    while i < i_end+3:
        if i >= len_timeline:
            break
        if timeline[i][NEED_FAST_ALL_IDX] == 0:
            i += 1
            continue

        i_tmp_beg = i
        i_tmp_end = i
        no_stop = 0
        for j in range(i_tmp_beg+1, i_end+3):
            if j >= len_timeline:
                break
            if timeline[j][NEED_FAST_ALL_IDX] == 0:
                no_stop += 1
                if no_stop == 50:
                    break
                continue
            no_stop = 0
            i_tmp_end = j

        if i_need_beg == -1 or i_need_end - i_need_beg < i_tmp_end - i_tmp_beg:
            i_need_beg = i_tmp_beg
            i_need_end = i_tmp_end

        i = i_tmp_end+1
    return i_need_beg, i_need_end


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


def get_all_need_usage_occupy_eff(timeline, i_beg, i_end, env='net'):
    if i_beg < 0:
        return -1, -1, -1, -1

    need_fast_total = 0
    usage_total = 0
    occupy_total = 0
    eff_u_total = 0
    for idx_unit in range(i_beg, i_end + 1):
        unit = timeline[idx_unit]
        need_fast_all = unit[NEED_FAST_ALL_IDX]
        alloc_all = unit[ALLOC_ALL_IDX]
        # usage_all = unit[USAGE_ALL_IDX] if env == 'net' else unit[ALLOC_ALL_IDX]
        usage_all = unit[USAGE_ALL_IDX]
        occupy_all = max(alloc_all, usage_all)
        eff_u_all = unit[EFF_U_ALL_IDX]

        need_fast_total += need_fast_all
        usage_total += usage_all
        occupy_total += occupy_all
        eff_u_total += eff_u_all
    return need_fast_total, usage_total, occupy_total, eff_u_total


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


def get_an_ua_eu_en_entropy(timeline, i_beg, i_end, span=1):
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
        
        an_ratio = min(100, int(alloc_item/need_item * 100 + 0.5)) if need_item > 0 else 999999999999999999999999999
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


if __name__ == "__main__":
    grandParent = sys.argv[1]

    parents = []
    for parent in os.listdir(grandParent):
        path = os.path.join(grandParent, parent)
        if not os.path.isdir(path):
            continue
        # if "spb" in parent:
        #     continue
        parents.append(path)

    p = Pool(4)
    res_li = []
    for parent in parents:
        # if '0429175153-' not in parent:
        # if re.search(r'net-[0-9]+-50-1-', parent) is None and \
        #    re.search(r'spb-[0-9]+-50-1', parent) is None:
        # continue
        res = p.apply_async(calculate_one, (parent,))
        res_li.append(res)

    suffix = hashlib.md5(grandParent.encode('utf-8')).hexdigest()[:6]
    out_filepath = os.path.join(
        grandParent, f'on_uo_eu_en_entropy_v6-{suffix}.csv')
    with open(out_filepath, 'w+') as f:
        print(out_filepath)
        # f.write(','.join(['t_run', 'env', 'no_task', 'config', 'acc_speed', 'peak_task', 'un', 'uo_alloc', 'uo_var_alloc', 'acc_alloc', 'acc_var_alloc', 'ur_need', 'ur_alloc', 'yield', 'goodput', 'need_beg', 'need_len', 'alloc_len'])+'\n')
        f.write(','.join([
            't_run', 'env', 'no_task', 'config', 'acc_speed', 'peak_task',

            '占用/需求_need', '使用/占用_need', '有效/使用_need', '有效/需求_need',
            '占用需求熵_need', '占用需求熵_p_need',
            '使用率熵_need', '使用率熵_p_need',
            '有效使用熵_need', '有效使用熵_p_need',
            '有效需求熵_need', '有效需求熵_p_need',
            
            '占用/需求_alloc', '使用/占用_alloc', '有效/使用_alloc', '有效/需求_alloc',
            '占用需求熵_alloc', '占用需求熵_p_alloc',
            '使用率熵_alloc', '使用率熵_p_alloc',
            '有效使用熵_alloc', '有效使用熵_p_alloc',
            '有效需求熵_alloc', '有效需求熵_p_alloc',

            'yield', 'goodput',
            'need_beg', 'need_len', 'alloc_len'
        ])+'\n')
        # f.write(','.join([
        #     't_run', 'env', 'no_task', 'config', 'acc_speed', 'peak_task',

        #     '分配需求比_need', '分配需求比标准差_need',
        #     '使用分配比_need', '使用分配比标准差_need',
        #     '有效使用率_need', '有效使用率_标准差_need',
            
        #     '分配需求比_alloc', '分配需求比标准差_alloc',
        #     '使用分配比_alloc', '使用分配比标准差_alloc',
        #     '有效使用率_alloc', '有效使用率_标准差_alloc',

        #     'yield', 'goodput',
        #     'need_beg', 'need_len', 'alloc_len'
        # ])+'\n')
        for res in res_li:
            r = res.get()
            if r == 0:
                continue
            print(r)
            f.write(r+'\n')
