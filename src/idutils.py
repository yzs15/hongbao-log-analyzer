ID_LEN = 20


def client_id(id):
    return (id >> ID_LEN) & ((1 << ID_LEN) - 1)


def server_id(id):
    return id & ((1 << ID_LEN) - 1)


def message_id(mid, sender):
    return mid << (ID_LEN * 2) | sender


def device_id(sid, cid):
    return cid << ID_LEN | sid
