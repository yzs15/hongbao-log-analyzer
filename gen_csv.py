
import json
import sys
import os

net_config = "/Users/jian/Workspace/Research/hongbao-log/configs/bjnj/log-net.json"
spb_config = "/Users/jian/Workspace/Research/hongbao-log/configs/bjnj/log-spb.json"
#{ratio:{peak:{type:[]}}}
data = {}

def record(task_num, peak , ratio , type, file_path):
    try:
        f = open(file_path)
        line = f.readlines()[0]

        line_li = line.replace("\n", "").split(",")
        # y100 = line_li[-6]
        # y50 = line_li[-5]
        # y20 = line_li[-4]
        # g100 =line_li[-3]
        # g50 =line_li[-2]
        # g20 = line_li[-1]
        print(line_li)
        if not data.__contains__(ratio):
            data[ratio] = {}
        if not data[ratio].__contains__(peak):
            data[ratio][peak] = {}
        if not data[ratio][peak].__contains__(type):
            data[ratio][peak][type] = []
        data[ratio][peak][type].append(line_li[-7:])
    except Exception as err:
        print(err)

def gen_csv_one(parent):
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
    print("net", is_net, "spb", is_spb)
    if is_net:  
        base = os.path.basename(parent)
        # print(base)
        base_list = base.split("-")
        task_num = base_list[2]
        peak = base_list[3]
        ratio = base_list[4]
        type = base_list[5]
        for file in os.listdir(parent):
            if not os.path.isdir(parent):
                continue
            if  not "net" in file:
                continue
            log_path = os.path.join(parent,file)
            file_path = os.path.join(log_path, "result.csv")
            record(task_num, peak, ratio, type, file_path)
    
    if is_spb:  
        base = os.path.basename(parent)
        print(base)
        base_list = base.split("-")
        task_num = base_list[2]
        peak = base_list[3]
        ratio = base_list[4]
        type = "spb"
        for file in os.listdir(parent):
            if not os.path.isdir(parent):
                continue
            if  not "spb" in file:
                continue
            log_path = os.path.join(parent,file)
            file_path = os.path.join(log_path, "result.csv")
            record(task_num, peak, ratio, type, file_path)
            
    
    return 0
if __name__=="__main__":
    grandParent=sys.argv[1]
    parents = []
    for parent in os.listdir(grandParent):
        path = os.path.join(grandParent, parent)
        if not os.path.isdir(path):
            continue
        if "net" not in parent and "spb" not in parent:
            continue
        parents.append(path)

    for parent in parents:
        gen_csv_one(parent)
    import pprint
    pprint.pprint(data["1"])
    f = open(os.path.join(grandParent,"final.csv"), "w")
    for ration in data:
        f.write(ration+"\n")
        for peak_int in range(10, 180, 10):
            peak = str(peak_int)
            
            if not data[ration].__contains__(peak):
                continue
            f.write("%s"%peak)
            for type in ["10mC20C60%", "1C2C60%", "4C8C10%", "spb"]:
                if data[ration][peak].__contains__(type):
                    res =  data[ration][peak][type][-1]
                    f.write(",")
                    f.write(",".join(res))
                else:
                    f.write(",?,?,?,?,?,?")
            f.write("\n")
        f.write("\n\n") 


