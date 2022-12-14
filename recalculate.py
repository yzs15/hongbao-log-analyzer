from multiprocessing import Pool, parent_process
import sys
import os
from fackmain import start
from check_network_valid import load_net_valid

net_config = "configs/bjnj/log-net.json"
spb_config = "configs/bjnj/log-spb.json"

def recalculate_one(parent):
    is_net = False
    is_spb = False
    if not os.path.isdir(parent):
        return 0
    if "net" in parent:
        is_net = True
    if "spb" in parent:
        is_spb = True
    if not is_net and not is_spb:
        return 0
    # print("net", is_net, "spb", is_spb)
    if is_net:  
        base = os.path.basename(parent)
        # print(base)
        base_list = base.split("-")
        task_num = base_list[2]
        # peak = base_list[3]
        # ratio = base_list[4]
        # type = base[5]
        for file in os.listdir(parent):
            log_path = os.path.join(parent,file)
            if not os.path.isdir(log_path):
                continue
            if  not "net" in file:
                continue
            
            # print(task_num, peak, ratio, type)
            # print(log_path)
            # start(net_config, log_path)
            # if "-10-" in log_path:
                # print(log_path)
            start(net_config, log_path)
    
    if is_spb:  
        base = os.path.basename(parent)
        print(base)
        base_list = base.split("-")
        task_num = base_list[2]
        # peak = base_list[3]
        # ratio = base_list[4]
        type = "spb"
        for file in os.listdir(parent):
            log_path = os.path.join(parent,file)
            if not os.path.isdir(log_path):
                continue
            if  not "spb" in file:
                continue
            
            # print(task_num, peak, ratio, type)
            print(log_path)
            # /Volumes/Elements/logs-yuzishu-4-17-valid-linear-no-noise-k8s-limit-exp3/0418014847-spb-76800-2-1
            # if not "0501205250-spb-320000" in log_path:
            #     continue
            start(spb_config, log_path)
    return 0


def recalculate_not_exist(parent):
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
    
    if os.path.exists(os.path.join(log_dirpath, 'net.jpg')) or \
        os.path.exists(os.path.join(log_dirpath, 'spb.jpg')):
            result_path = os.path.join(log_dirpath,"result.csv")
            if os.path.exists(result_path):
                t =  os.path.getmtime(result_path)
                import time
                recent = time.strptime("2022-11-14 19:00:00", "%Y-%m-%d %H:%M:%S")
                if t > time.mktime(recent): 
                    print(os.getpid(), '====> skip for already update', parent)
                    return 
    # recalculate_one(parent)
    from calculate_need_usage_alloc import get_mac_parent
    valid = load_net_valid(parent) 
    
    if (get_mac_parent(parent) in  valid):
        valid_info = valid[get_mac_parent(parent)]
        if valid_info[0]:
            print(os.getpid(), '====> recalculate', parent)
            recalculate_one(parent)
        else:
            print(os.getpid(), '====> skip for net not valid', parent)
    else:
        print(os.getpid(), '====> skip for net not record', parent)
    return 0


if __name__=="__main__":
    grandParent=sys.argv[1]
    parents = []
    for parent in os.listdir(grandParent):
        path = os.path.join(grandParent, parent)
        if not os.path.isdir(path):
            continue
        if 'not' in parent:
            continue
        parents.append(path)
    
    p = Pool(1)
    res_li = []
    parents.sort()
    # parents.reverse()
    for parent in parents:
        res = p.apply_async(recalculate_not_exist, (parent,))
        res_li.append(res)
    for res in res_li:
        res.get()
