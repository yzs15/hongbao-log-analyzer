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


async def serve():
    uri = "ws://{}/?mac=02:42:ac:14:00:01&expid=3".format(WS_END)
    async with websockets.connect(uri) as websocket:
        # 建立 WebSocket 链接后，接收自己的ID信息
        raw = await websocket.recv()
        msg = Message.from_bytes(raw)
        if msg.type() != MessageType.Name.value:
            print("don't receive name message")
            return
        my_id = msg.receiver()
        print("your id is {}".format(my_id))

        last_time = time() * 1e9
        mid = 1
        while True:
            # 接收开始进行分析的通知
            raw = await websocket.recv()
            msg = Message.from_bytes(raw)
            if msg.type() != MessageType.Text.value:
                print("don't react for text message")
                print(str(msg))
                continue
            if msg.receiver() != my_id:
                print("receive a broadcast message")
                continue
            print(msg.body().decode("utf-8"))

            # last_time = time() * 1e9
            analyzer = Analyzer(ZMQ_END, mid, my_id, msg.sender(), LOG_SERVERS, ENV, 0)
            last_time = analyzer.run()
            print("last time: ", last_time)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("please use config to run")
    else:
        with open(sys.argv[1], "r") as f:
            text = f.read()
            conf = json.loads(text)
            WS_END = conf["msws"]
            ZMQ_END = conf["mszmq"]
            LOG_SERVERS = conf["loggers"]
            ENV = conf["env"]
            print(WS_END, ZMQ_END, LOG_SERVERS)
        asyncio.run(serve())
