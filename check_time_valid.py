import os
import sys
from calculate_need import check_noise, check_warm, get_location, check_person
from src.analyzer_local import load_logs_from_dir, msg_id_dot2int

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

    filenames = os.listdir(log_dirpath)
    for filename in filenames:
        name, ext = os.path.splitext(filename)
        if name.find("log") != -1 or ext != ".txt":
            continue

        with open(os.path.join(log_dirpath, filename), "r") as f:
            while True:
                line = f.readline().strip()
                if line is None or line == "":
                    break
                
                items = line.split(",")
                if len(items) < 4:
                    continue

                if '.' in items[4]:
                    msg_id = msg_id_dot2int(items[4])
                else:
                    msg_id = int(items[4])
                if check_noise(msg_id) or check_warm(msg_id) or check_person(msg_id):
                    continue

                time = int(items[3])
                if time < 1600000000000000000:
                    print(items)
                    print(log_dirpath)
                    print(filename)
                    print(line)
                    break


if __name__=="__main__":
    grandParent = sys.argv[1]
    
    parents = []
    for parent in os.listdir(grandParent):
        path = os.path.join(grandParent, parent)
        if not os.path.isdir(path):
            continue
        # if "spb" in parent:
        #     continue
        if 'not' in parent:
            continue
        
        check(path)
    