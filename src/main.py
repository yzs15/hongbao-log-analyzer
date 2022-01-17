import sys
import asyncio
import websockets

from src.message import Message, MessageType
from src.analyzer import Analyzer

WS_END = ""
ZMQ_END = ""

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
            print(str(msg.body()))

            analyzer = Analyzer(ZMQ_END, mid, my_id, msg.sender())
            analyzer.start()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage main.py WS_END ZMQ_END")
    else:
        WS_END = sys.argv[1]
        ZMQ_END = sys.argv[2]
        asyncio.run(serve())
