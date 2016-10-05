import selectors

class Channel:
    def __init__(self, name):
        """Channel class constructor"""
        self.name = ""
        self.users = list()

        self.name = name
