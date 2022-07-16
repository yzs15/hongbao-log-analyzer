import os
import sys
from calculate_need import check_noise, check_warm, get_location, check_person
from src.analyzer_local import load_logs_from_dir, msg_id_dot2int, msg_id_int2dot
from multiprocessing import Pool, Lock
from calculate_need_usage_alloc import load_comp_ranges, get_mac_parent
import json
import hashlib

def load_net_valid(parent):
    if os.path.exists(os.path.join(parent, '../../net_valid_rets.json')):
        with open(os.path.join(parent, '../../net_valid_rets.json'), 'r') as f:
            return json.load(f)
    return {}

def dump_net_valid(parent, data):
    with open(os.path.join(parent, '../../net_valid_rets.json'), 'w') as f:
        json.dump(data, f, indent=2)

lock = Lock()
def check(parent):
    mac_parent = get_mac_parent(parent)
    with lock:
        net_valids = load_net_valid(parent)
    if mac_parent in net_valids:
        valid, no_err = net_valids[mac_parent]
        if valid == False:
            print(parent, no_err)
        return None
    
    log_dirpath = None
    for file in os.listdir(parent):
        if not os.path.isdir(os.path.join(parent, file)):
            continue
        if file.startswith('2022'):
            log_dirpath = os.path.join(parent, file)
            break
    if log_dirpath is None:
        print(parent, 'Not found log dirpath')
        return None

    if 'net' in parent:
        env = 'net'
    else:
        env = 'spb'
    
    with lock:
        comp_ranges = load_comp_ranges(parent)
    if mac_parent not in comp_ranges:
        return None
    ts_analysis = comp_ranges[mac_parent][3]

    suffix = hashlib.md5(mac_parent.encode('utf-8')).hexdigest()[:6]
    errs_file = open(os.path.join(parent, f'network_errs-{suffix}.csv'), 'w')

    no_err = 0
    msg_chains = load_logs_from_dir(log_dirpath, 0)
    for msg_id, logs in msg_chains:
        if check_noise(msg_id) or check_warm(msg_id) or check_person(msg_id):
            continue
        
        log_len = len(logs)
        location = get_location(msg_id)
        if location == 2:
            continue
        
        if env == 'net':
            if log_len < 5:
                continue
            if log_len == 5 and ts_analysis - logs[4].time > 50 * 1000 * 1000:
                err_msg_id = msg_id_int2dot(msg_id)
                err_msg = 'logs length equal to 5'
                errs_file.write(','.join([err_msg_id, err_msg, ""])+'\n')
                no_err += 1
            if log_len > 5 and logs[5].time - logs[4].time > 10 * 1000 * 1000 * 1000:
                comm_time = (logs[5].time - logs[4].time) / 1000000000.0
                err_msg_id = msg_id_int2dot(msg_id)
                err_msg = 'communication time greater than 10s'
                errs_file.write(','.join([err_msg_id, err_msg, str(comm_time)])+'\n')
                no_err += 1
        else:
            if log_len < 11:
                continue
            if log_len == 11 and ts_analysis - logs[10].time > 50 * 1000 * 1000:
                err_msg_id = msg_id_int2dot(msg_id)
                err_msg = 'logs length equal to 11'
                errs_file.write(','.join([err_msg_id, err_msg, ""])+'\n')
                no_err += 1
            if log_len > 11 and logs[11].time - logs[10].time > 10 * 1000 * 1000 * 1000:
                comm_time = (logs[5].time - logs[4].time) / 1000000000.0
                err_msg_id = msg_id_int2dot(msg_id)
                err_msg = 'communication time greater than 10s'
                errs_file.write(','.join([err_msg_id, err_msg, str(comm_time)])+'\n')
                no_err += 1
    errs_file.close()
    
    valid = no_err == 0
    if valid == False:
        print(parent, no_err)
    
    with lock:
        net_valids = load_net_valid(parent)
        net_valids[mac_parent] = [valid, no_err]
        dump_net_valid(parent, net_valids)
    return None
            
            
if __name__=="__main__":
    grandParent = sys.argv[1]
    
    p = Pool(2)
    res_li = []
    
    parents = []
    for parent in os.listdir(grandParent):
        path = os.path.join(grandParent, parent)
        if not os.path.isdir(path):
            continue
        if 'not' in parent:
            continue
        parents.append(path)
    
    parents.sort()
    for parent in parents:
        # if 'spb' not in parent:
        #     continue
        res = p.apply_async(check, (parent,))
        res_li.append(res)
        
    for res in res_li:
        s = res.get()
        if s is not None:
            print(s)