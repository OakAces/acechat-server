class User:
    def __init__(self, conn, addr):
        """User class constructor"""
        self.addr = ""
        self.username = ""
        self.channels = list()

        self.addr = addr
        self.conn = conn

    def has_username(self):
        return bool(self.username)
