import sys
import json

from src.message import Message, MessageType
from src.analyzer import Analyzer

WS_END = ""
ZMQ_END = ""
LOG_SERVERS = ""
ENV = ""
PREFIX = ""

def serve():
    analyzer = Analyzer(ZMQ_END,  1  , 2,3, LOG_SERVERS, ENV, 0)
    last_time = analyzer.fake_run(prefix=PREFIX)
    print("last time: ", last_time)

def task_character_ana():
    analyzer = Analyzer(ZMQ_END,  1  , 2,3, LOG_SERVERS, ENV, 0)
    last_time = analyzer.task_character_ana(prefix=PREFIX)
    print("last time: ", last_time)


def start(conf_path, prefix):
    global WS_END,ZMQ_END,LOG_SERVERS,ENV,PREFIX
    with open(conf_path, "r") as f:
        text = f.read()
        conf = json.loads(text)
        WS_END = conf["msws"]
        ZMQ_END = conf["mszmq"]
        LOG_SERVERS = conf["loggers"]
        ENV = conf["env"]
        PREFIX = prefix
    try:
        serve()
    except Exception as err:
        print("start error: %s" % err)
        f = open("log", "a")
        f.write(prefix+"\n")
        f.close()

def task_character(conf_path, prefix):
    global WS_END,ZMQ_END,LOG_SERVERS,ENV,PREFIX
    with open(conf_path, "r") as f:
        text = f.read()
        conf = json.loads(text)
        WS_END = conf["msws"]
        ZMQ_END = conf["mszmq"]
        LOG_SERVERS = conf["loggers"]
        ENV = conf["env"]
        PREFIX = prefix
    try:
        task_character_ana()
    except Exception as err:
        f = open("log", "a")
        f.write(prefix+"\n")
        f.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("please use config to run")
    else:
        with open(sys.argv[1], "r") as f:
            text = f.read()
            conf = json.loads(text)
            WS_END = conf["msws"]
            ZMQ_END = conf["mszmq"]
            LOG_SERVERS = conf["loggers"]
            ENV = conf["env"]
            PREFIX = sys.argv[2]
            print(WS_END, ZMQ_END, LOG_SERVERS)
        serve()
