from src.zmqutils import send
from src.message import Message, MessageType
from src.idutils import message_id, device_id
import time
import sys
import asyncio
import websockets

FULL = (1 << 8) - 1

WS_END = ""
ZMQ_END = ""


async def serve():
    uri = "ws://{}/?mac=02:42:af:14:00:01&expid=1".format(WS_END)
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
            continue
            # msg = Message.from_bytes(raw)
            # if msg.type() != MessageType.Text.value:
            #     print("don't react for text message")
            #     print(str(msg))
            #     continue
            # if msg.receiver() != my_id:
            #     print("receive a broadcast message")
            #     continue
            # print(msg.body().decode("utf-8"))


def make_test_msg():
    sender_id = device_id(2, 1)
    receiver_id = (1 << 40) - 1

    msg_id = message_id(1, sender_id)

    flag = (FULL-3).to_bytes(1, "little")
    content = flag + str.encode('开始测试')

    return Message(msg_id, sender_id, receiver_id, MessageType.Text, content)


def make_analysis_msg():
    sender_id = device_id(2, 1)
    receiver_id = device_id(2, 3)

    msg_id = message_id(2, sender_id)

    content = str.encode('开始分析')

    return Message(msg_id, sender_id, receiver_id, MessageType.Text, content)


def main():
    global ZMQ_END
    global WS_END

    env = sys.argv[1]
    test_time = int(sys.argv[2])
    print("env: ", env)
    print("test time:", test_time)

    # asyncio.run(serve())
    if env == "spb":  # spb
        ZMQ_END = "tcp://58.240.113.38:10021"
        # ZMQ_END = "tcp://10.208.104.3:8081"
        WS_END = "ws://10.208.104.3:8082"
    else:
        ZMQ_END = "tcp://58.240.113.38:10018"
        # ZMQ_END = "tcp://10.208.104.9:7071"
        WS_END = "ws://10.208.104.9:7072"

    test_msg = make_test_msg()
    ana_msg = make_analysis_msg()

    send(ZMQ_END, test_msg.to_bytes())
    time.sleep(test_time)
    send(ZMQ_END, ana_msg.to_bytes())

    # send(ZMQ_END, test_msg.to_bytes())
    # time.sleep(60)
    # send(ZMQ_END, ana_msg.to_bytes())

    time.sleep(10)


if __name__ == '__main__':
    main()