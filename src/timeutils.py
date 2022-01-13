from datetime import datetime


def str2stamp(s: str):
    splited = s.split(".")
    dts = '.'.join(splited[:-1])
    dt = datetime.strptime(dts, '%Y-%m-%dT%H:%M:%S')
    s = int(dt.timestamp())
    ns = int(splited[-1][:-1])
    return s * 1000000000 + ns
