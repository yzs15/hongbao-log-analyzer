from operator import imod
import os
import sys
grandParent = sys.argv[1]

def handle_net( parent, path, request):
    
    f = open(path)
    try:
        data = f.readlines()
    except:
        print(path)
        return
    ED = 0
    DD2 = 0
    N= 0
    D_list = []
    for line in data:
        l = line.split(",")
        cpu_usage = float(l[5]) / 100
        cpu_request = float(l[6]) * request
        try:
            D = (cpu_usage-cpu_request) / cpu_request
        except:
            print("ERROR", parent, N, l)
            exit(0)
        D_list.append(D)
        ED += D
        N += 1
    ED = ED / N
    for line in data:
        l = line.split(",")
        cpu_usage = float(l[5]) / 100
        cpu_request = float(l[6]) * request
        D = (cpu_usage-cpu_request) / cpu_request
        DD2 += (D-ED)**2
    DD = (DD2 / N) ** 0.5
    D_list.sort()
    print(parent, N*0.1, ED, DD, D_list[N//4],  D_list[3*N//4])


def handle_spb(parent, path):
    
   
    f = open(path)
    data = f.readlines()
    ED = 0
    DD2 = 0
    N= 0
    D_list = []
    for line in data:
        l = line.split(",")
        # print(parent, line)
        cpu_usage = float(l[6]) 
        cpu_request = float(l[5]) 
        try:
            if cpu_usage-cpu_request == 0:
                D = 0
            else:
                D = (cpu_usage-cpu_request) / cpu_request
        except:
            print("ERROR", parent, N, l)
            exit(0)
        D_list.append(D)
        ED += D
        N += 1
    ED = ED / N
    for line in data:
        l = line.split(",")
        cpu_usage = float(l[6])
        cpu_request = float(l[5])
        if cpu_usage-cpu_request == 0:
            D = 0
        else:
            D = (cpu_usage-cpu_request) / cpu_request
        DD2 += (D-ED)**2
    DD = (DD2 / N) ** 0.5
    D_list.sort()
    print(parent, N*0.1, ED, DD, D_list[N//4],  D_list[3*N//4])
    

# for parent in os.listdir(grandParent):
#     if "net" in parent:
#         request = parent.split("-")
#         if len(request) != 5:
#             continue
#         request = int(request[3][0:2].replace("C","000")) / 1000
#         path = os.path.join(grandParent, parent, "k8s_load_cpu_300ms.csv")
#         handle_net(parent, path, request)
#     if "spb" in parent:
#         path = os.path.join(grandParent, parent, "ts_cpu_alloc_100ms.csv")
#         handle_spb(parent, path)

for parent in os.listdir(grandParent):
    if "k8s" in parent:
        request = parent.split("-")
        # print(request)
        if len(request) != 4:
            continue
        request = int(request[3][0:2].replace("c","000")) / 1000
        print(request)
        path = os.path.join(grandParent, parent)
        handle_net(parent, path, request)
    if "spb" in parent:
        path = os.path.join(grandParent, parent)
        handle_spb(parent, path)