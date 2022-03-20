from src.analyzer import Analyzer
import os
import sys


def parse_dir_log(log_path):
    analyzer = Analyzer("", 0, 0, 0, [], "spb", 0)

    paths = os.listdir(log_path)
    for path in paths:
        dirpath = os.path.join(log_path, path)
        if not os.path.isdir(dirpath):
            continue
        print(dirpath)

        if "spb" in path:
            analyzer.env = "spb"
        else:
            analyzer.env = "net"
        analyzer.run_local(dirpath)


if __name__ == "__main__":
    # parse_dir_log("./logs-20220308")
    # parse_dir_log("./logs-20220309")
    # parse_dir_log("./logs")

    dirpath = sys.argv[1]

    analyzer = Analyzer("", 0, 0, 0, [], "spb", 0)
    if "spb" in dirpath:
        analyzer.env = "spb"
    else:
        analyzer.env = "net"

    analyzer.run_local(dirpath)

    # 20220309141722-spb-1600
    # 20220309120810-spb-3200
    # 20220309115933-spb-6400
