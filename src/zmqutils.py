import zmq


def send(endpoint, raw):
    context = zmq.Context()

    socket = context.socket(zmq.PUSH)
    socket.connect(endpoint)
    socket.send(raw)
    print("send a message, size: {}".format(len(raw)))
