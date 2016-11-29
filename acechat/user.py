class User:
    def __init__(self, conn, path):
        """User class constructor"""
        self.path = ""
        self.username = ""

        self.path = path
        self.conn = conn

    def set_username(self, username):
        self.username = username

    def has_username(self):
        return bool(self.username)
