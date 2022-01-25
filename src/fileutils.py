from urllib.parse import urlparse


def save_logs(prefix, server, logs):
    uri = urlparse(server)
    server_name = uri.hostname
    port = uri.port
    filename = "{}/{}-{}.txt".format(prefix, server_name, port)
    with open(filename, "x") as f:
        f.write(logs)