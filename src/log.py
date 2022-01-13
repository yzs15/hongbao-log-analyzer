class Log:
    def __init__(self, row):
        cols = row.split(',')
        self.sender = cols[0]
        self.receiver = cols[1]
        self.logger = cols[2]
        self.timestamp = int(cols[3])
        self.message_id = cols[4]
        self.event = cols[5]