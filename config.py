class ConnectionConfig:
    def __init__(self, host="", port=5672, username="", password="", queue="", vhost="/", prefetch_count=10):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.queue = queue
        self.vhost = vhost
        self.prefetch_count = prefetch_count