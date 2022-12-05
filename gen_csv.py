
import json
import sys
import os

net_config = "/Users/jian/Workspace/Research/hongbao-log/configs/bjnj/log-net.json"
spb_config = "/Users/jian/Workspace/Research/hongbao-log/configs/bjnj/log-spb.json"
#{ratio:{peak:{type:[]}}}
data = {}

def record(task_num, peak , ratio , type, file_path, utility):
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
        data[ratio][peak][type].append(line_li[-7:]+[utility])
    except Exception as err:
        print(err)
def load_util(parent):
    alloc_path = os.path.join(parent, "ts_cpu_alloc_100ms.csv")
    uasge_path = os.path.join(parent, "ts_cpu_usage_100ms.csv")
    def load_cpu_use(file_path):
        f = open(file_path)
        use = 0
        lines = f.readlines()
        

        for line in lines:
            line = line.replace("\n", "")
            if line[-1] == ",":
                line = line[0:-1]
            datas = line.split(",")
            use += float(datas[-1])
        return use
    alloc = load_cpu_use(alloc_path)
    uasge = load_cpu_use(uasge_path)
    return str(uasge / alloc)
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
        utility = "0"

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
            record(task_num, peak, ratio, type, file_path, utility)
    
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
            try:
                utility = load_util(parent)
            except:
                utility = "0"
            file_path = os.path.join(log_path, "result.csv")
            record(task_num, peak, ratio, type, file_path, utility)
            
    
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
    # pprint.pprint(data["1"])
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
                    max_util = 0
                    min_util = 1000
                    average_util = 0
                    num = 0
                    for info in  data[ration][peak][type]:
                        res = info
                        max_util = max(max_util, float(res[-1]))
                        min_util = min(min_util, float(res[-1]))
                        average_util +=  float(res[-1])
                        num+= 1
                    print(res)
                    qos_yield = float(res[1])*0.5 + float(res[2])*13/32 + float(res[3])*3/32
                    qos_goodput = float(res[4]) + float(res[5]) + float(res[6])
                    res = [res[0]]
                    res.append(str(qos_yield))
                    res.append(str(qos_goodput))
                    res.append(str(average_util / num))
                    res.append(str(max_util))
                    res.append(str(min_util))
                    f.write(",")
                    f.write(",".join(res))
                else:
                    f.write(",?,?,? ,?,?,?")
                    # f.write(",? ,?,?,? ,?,?,? ,?,?,?,?,?")
            f.write("\n")
        f.write("\n\n") 


