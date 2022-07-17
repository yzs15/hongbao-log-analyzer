import sys
import os
import json
from datetime import datetime
import requests
from urllib.parse import urlparse
from calculate_need_usage_alloc import extract_meta
from multiprocessing import Pool

net_config = "configs/bjnj/log-net.json"
spb_config = "configs/bjnj/log-spb.json"

server_map = {
    "http://192.168.143.4:8080": 'http://58.240.113.38:10009',
    "http://159.226.41.229:7103": 'http://10.208.104.9:8084',
    "http://159.226.41.229:8084": 'http://10.208.104.3:8084',
    
    "http://192.168.143.1:8083": 'http://58.240.113.38:10022',
    "http://159.226.41.229:8083": 'http://10.208.104.3:8083',
    "http://159.226.41.229:7065": 'http://10.208.104.3:7065',
    "http://159.226.41.229:7104": 'http://10.208.104.9:8080',
    "http://192.168.143.2:8080": 'http://58.240.113.38:10005',
    "http://192.168.143.1:8080": 'http://58.240.113.38:10003'
}

def save_logs(log_dirpath, server, logs):
    uri = urlparse(server)
    server_name = uri.hostname
    port = uri.port
    filename = "{}/{}-{}.txt".format(log_dirpath, server_name, port)
    with open(filename, "x") as f:
        f.write(logs)

def dl_from_server(log_dirpath, server):
    log_text = ""
    server_redict = server_map[server]
    print("start request log: ", server_redict)
    resp = requests.get(server_redict)
    print("end request log: ", server_redict)
    log_text += resp.text.strip() + '\n'
    save_logs(log_dirpath, server, log_text)
    return 0

def download(parent):
    env = 'net' if 'net' in parent else 'spb'
    
    conf_path = net_config if env == 'net' else spb_config
    with open(conf_path, "r") as f:
        text = f.read()
        conf = json.loads(text)
        LOG_SERVERS = conf["loggers"]

    _, _, no_task, _, _, _ = extract_meta(parent)

    now = datetime.now()
    log_dirname = "{0:04d}{1:02d}{2:02d}{3:02d}{4:02d}{5:02d}-{6}-{7:d}".format(
        now.year, now.month, now.day, now.hour, now.minute, now.second, env, int(no_task))
    log_dirpath = os.path.join(parent, log_dirname)
    os.mkdir(log_dirpath)
    
    p = Pool(6)
    rets = []
    for server in LOG_SERVERS:
        ret = p.apply_async(dl_from_server, (log_dirpath, server,))
        rets.append(ret)
    for ret in rets:
        ret.get()
    return 0

if __name__=="__main__":
    parent = sys.argv[1]
    download(parent)
