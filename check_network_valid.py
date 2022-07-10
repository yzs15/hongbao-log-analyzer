import os
import sys
from calculate_need import check_noise, check_warm, get_location, check_person
from src.analyzer_local import load_logs_from_dir, msg_id_dot2int, msg_id_int2dot
from multiprocessing import Pool, Lock
from calculate_need_usage_alloc import load_comp_ranges, get_mac_parent

lock = Lock()
def check(parent):
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

    if 'net' in parent:
        env = 'net'
    else:
        env = 'spb'

    
    with lock:
        comp_ranges = load_comp_ranges(parent)
    mac_parent = get_mac_parent(parent)
    ts_analysis = comp_ranges[mac_parent][3]

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
                return '\t'.join([parent, msg_id_int2dot(msg_id), 'logs length equal to 5'])
            if log_len > 5 and logs[5].time - logs[4].time > 10 * 1000 * 1000 * 1000:
                return '\t'.join([parent, msg_id_int2dot(msg_id), 'communication time greater than 10s'])
        else:
            if log_len < 11:
                continue
            if log_len == 11 and ts_analysis - logs[10].time > 50 * 1000 * 1000:
                return '\t'.join([parent, msg_id_int2dot(msg_id), 'logs length equal to 11'])
            if log_len > 11 and logs[11].time - logs[10].time > 10 * 1000 * 1000 * 1000:
                return '\t'.join([parent, msg_id_int2dot(msg_id), 'communication time greater than 10s'])
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
        res = p.apply_async(check, (parent,))
        res_li.append(res)
        
    for res in res_li:
        s = res.get()
        if s is not None:
            print(s)