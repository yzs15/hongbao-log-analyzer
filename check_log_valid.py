from multiprocessing import Pool
import os
import sys

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
        return 0
    
    if not os.path.exists(os.path.join(log_dirpath, 'net.jpg')) and \
        not os.path.exists(os.path.join(log_dirpath, 'spb.jpg')):
            os.rename(parent, parent+'not')
            return 0
    
    if not os.path.exists(os.path.join(parent, 'ts-cpu')) and \
        not os.path.exists(os.path.join(parent, 'k8s-cpu')):
            os.rename(parent, parent+'not')
            return 0
        
    if os.path.exists(os.path.join(parent, 'k8s-cpu')):
        return 0

    print('====> ', parent)
    if not os.path.exists(os.path.join(parent, 'ts_cpu_alloc_100ms.csv')):
        os.system(f'python3 ./src/ts_cpu_alloc.py {log_dirpath}')
    if not os.path.exists(os.path.join(parent, 'ts_cpu_usage_100ms.csv')):
        ts_cpu_dir = os.path.join(parent, 'ts-cpu')
        os.system(f'python3 ./src/ts_cpu_usage.py {ts_cpu_dir} 100')
    
    if not os.path.exists(os.path.join(parent, 'ts_cpu_alloc_100ms.csv')) or \
        not os.path.exists(os.path.join(parent, 'ts_cpu_usage_100ms.csv')):
            os.rename(parent, parent+'not')
            return 0
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
    
    p = Pool(4)
    rets = []
    parents.sort()
    # parents.reverse()
    for parent in parents:
        ret = p.apply_async(check, (parent,))
        rets.append(ret)
    for ret in rets:
        ret.get()