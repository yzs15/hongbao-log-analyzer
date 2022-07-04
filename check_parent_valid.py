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
        return False    
    
    if not os.path.exists(os.path.join(parent, 'ts-cpu')) and \
        not os.path.exists(os.path.join(parent, 'k8s-cpu')):
            return False
    
    if not os.path.exists(os.path.join(log_dirpath, 'spb.jpg')) and \
        not os.path.exists(os.path.join(parent, 'k8s-cpu')):
            return False
    
    return True
    

if __name__ == "__main__":
    grandParent = sys.argv[1]

    for parent in os.listdir(grandParent):
        path = os.path.join(grandParent, parent)
        if not os.path.isdir(path):
            continue
        # if "spb" in parent:
        #     continue
        parent_dir = os.path.join(grandParent, parent)
        if not check(parent_dir):
            print(parent_dir, ' is invalid !!!!')
            if 'not' not in parent_dir:
                os.rename(parent_dir, parent_dir+'not')