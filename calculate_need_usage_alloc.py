from multiprocessing import Pool
import sys
import os
import re

from calculate_need import calculate_need
from src.k8s_cpu_utilization import list_total_cpu, compress_final_data

time_interval = 100 * 1000 * 1000


def calculate_usage_alloc(env, parent, time_interval):
    if env == 'net':
        grps = re.search(r'([0-9m]+)C(.*)C', parent)
        s_request = grps.group(1)
        s_limit = grps.group(2)
        if s_request == '10m':
            request = 0.01
        else:
            request = int(s_request)
        limit = int(s_limit)

        cpu_dirpath = os.path.join(parent, 'k8s-cpu')
        total_date = list_total_cpu(cpu_dirpath, noise=False)
        ini_timeline = compress_final_data(total_date, time_interval // 1000000)

        timeline = []
        for unit in ini_timeline:
            record = [0, 0, 0, 0, 0, 0, 0]
            record[0] = unit[0]
            record[1:4] = unit[2], unit[4], unit[6]
            record[4:7] = unit[1], unit[3], unit[5]

            record[1:4] = map(lambda x: x * request, record[1:4])
            record[4:7] = map(lambda x: x / (time_interval//1000000), record[4:7])

            timeline.append(record)
    
    else:
        # 读取使用CPU
        filename = f'ts_cpu_usage_{time_interval//1000000}ms.csv'
        filepath = os.path.join(parent, filename)
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
    f.write('ts,need_fast_bj,need_fast_nj,need_fast_all,need_slow_bj,need_slow_nj,need_slow_all,alloc_bj,alloc_nj,alloc_all,usage_bj,usage_nj,usage_all\n')
    for rec in timeline:
        f.write(','.join(map(str, rec))+'\n')
    f.close()


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
    
    if not os.path.exists(os.path.join(parent, 'k8s-cpu')) and not os.path.exists(os.path.join(parent, 'ts-cpu')):
        print('Not found k8s-cpu or ts-cpu')
        return 0

    need_timeline = calculate_need(parent, env, time_interval)
    alloc_usage_timeline = calculate_usage_alloc(env, parent, time_interval)

    i_need = 0
    i_au = 0
    timeline = []
    while i_need < len(need_timeline) and i_au < len(alloc_usage_timeline):
        record = [0] * 13
        ts_need = need_timeline[i_need][0] % 1000000
        ts_au = alloc_usage_timeline[i_au][0] % 1000000
        if ts_need <= ts_au:
            record[0] = ts_need
            record[1:7] = need_timeline[i_need][1:]
            i_need += 1
        if ts_au <= ts_need:
            record[0] = ts_au
            record[7:] = alloc_usage_timeline[i_au][1:]
            i_au += 1
        timeline.append(record)
    while i_need < len(need_timeline):
        record = [0] * 13
        ts_need = need_timeline[i_need][0] % 1000000
        record[0] = ts_need
        record[1:7] = need_timeline[i_need][1:]
        i_need += 1
        timeline.append(record)
    while i_au < len(alloc_usage_timeline):
        record = [0] * 13
        ts_au = alloc_usage_timeline[i_au][0] % 1000000
        record[0] = ts_au
        record[7:] = alloc_usage_timeline[i_au][1:]
        i_au += 1
        timeline.append(record)
    
    out_filepath = os.path.join(parent, f"{env}_nau_{time_interval//1000000}_msg_recive.csv")
    print(out_filepath)
    output_timeline(timeline, out_filepath)
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
