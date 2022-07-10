from multiprocessing import Pool, parent_process
import sys
import os
from fackmain import start
net_config = "/Users/jian/Workspace/Research/hongbao-log/configs/bjnj/log-net.json"
spb_config = "/Users/jian/Workspace/Research/hongbao-log/configs/bjnj/log-spb.json"

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
            if not os.path.isdir(parent):
                continue
            if  not "net" in file:
                continue
            log_path = os.path.join(parent,file)
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
            if not os.path.isdir(parent):
                continue
            if  not "spb" in file:
                continue
            log_path = os.path.join(parent,file)
            # print(task_num, peak, ratio, type)
            print(log_path)
            # /Volumes/Elements/logs-yuzishu-4-17-valid-linear-no-noise-k8s-limit-exp3/0418014847-spb-76800-2-1
            # if not "0501205250-spb-320000" in log_path:
            #     continue
            start(spb_config, log_path)
            
    
    return 0
if __name__=="__main__":
    f = open("log", "w")
    f.close()
    grandParent=sys.argv[1]
    parents = []
    for parent in os.listdir(grandParent):
        path = os.path.join(grandParent, parent)
        if not os.path.isdir(path):
            continue
        if "net" not in parent and "spb" not in parent:
            continue
        parents.append(path)
    
    p = Pool(1)
    res_li = []
    for parent in parents:
        res = p.apply_async(recalculate_one, (parent,))
        res_li.append(res)
    for res in res_li:
        res.get()
