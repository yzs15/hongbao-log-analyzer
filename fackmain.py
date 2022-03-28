import sys
import json
import asyncio
import websockets
from time import time

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
