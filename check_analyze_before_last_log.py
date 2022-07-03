import os
import sys
from calculate_need import calculate_need, check_noise, check_warm, get_location, check_person
from src.analyzer_local import load_logs_from_dir
from src.analyzer import event_log

def check(parent):
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
    msg_chains = load_logs_from_dir(log_dirpath, 0)  #type: list[list[(int, event_log)]]
    
    end_time = -1
    analyze_time = -1
    for msg_id, logs in msg_chains:
        if get_location(msg_id) > 2:  # invalid message id
            continue
        if len(logs) < 1:  # 没有到 msg svr 发出
            # print('Skip for length')
            continue
        if check_noise(msg_id) or check_warm(msg_id):
            # print(f'Skip for noise:{check_noise(msg_id)} warm:{check_warm(msg_id)}')
            continue
        
        if check_person(msg_id):
            analyze_time = logs[0].time
            continue
        
        if end_time == -1 or logs[len(logs)-1].time > end_time:
            end_time = logs[len(logs)-1].time
    
    print(parent)
    print("\t", end_time, analyze_time, (analyze_time-end_time)/1000000, sep='\t')

if __name__ == "__main__":
    grandParent = sys.argv[1]

    for parent in os.listdir(grandParent):
        path = os.path.join(grandParent, parent)
        if not os.path.isdir(path):
            continue
        # if "spb" in parent:
        #     continue
        check(os.path.join(grandParent, parent))