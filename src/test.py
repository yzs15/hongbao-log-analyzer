from src.analyzer import Analyzer

LOG_SERVERS = [
    "http://58.240.113.38:10022",
    "http://10.208.104.3:8083",

    "http://10.208.104.3:7065",
    "http://10.208.104.9:8080",
    "http://58.240.113.38:10005",
    "http://58.240.113.38:10003"
]
ENV = "spb"

analyzer = Analyzer("", 0, 0, 0, LOG_SERVERS, ENV, 0)
analyzer.run()
