import selectors
import json
from json.decoder import JSONDecodeError
import socket

from acechat.user import User

class Server:
    def __init__(self, addr, port):
        """Server class constructor"""
        self.users = list()
        self.channels = dict()

        self.addr = addr
        self.port = port
        self.sock = socket.socket()
        self.sel = selectors.DefaultSelector()

        self.sock.bind((addr, port))
        self.sock.listen(5)
        self.sock.setblocking(True)

        data = {"newconn": True, "user": None}
        self.sel.register(self.sock, selectors.EVENT_READ, data)

    def new_connection(self, key):
        """set up a new connection"""
        sock = key.fileobj

        conn, addr = sock.accept()
        user = User(conn, addr)

        self.users.append(user)

        self.sel.register(
                sock,
                selectors.EVENT_READ,
                {"newconn": False, "user": user}
                )

    def recv_data(self, key):
        """Receive incoming json objects from a user"""
        user = key.data["user"]
        conn = key.fileobj
        data = conn.recv(4096)
        lines = user.data.splitlines()
        for line in lines:
            try:
                obj = json.loads(line)
                self.process_cmd(user, obj)
            except JSONDecodeError as e:
                print(e)

    def process_cmd(self, user, obj):
        """Process a json object from a user"""

        try:
            assert "command" in obj
            assert isinstance(obj["command"], str)
            assert "args" in obj
            assert isinstance(obj["args"], list)
            cmd = obj["command"]

            cmd_funcs = {
                    "USER": self.cmd_user,
                    "USERLIST": self.cmd_userlist,
                    "MSG": self.cmd_msg,
                    "PRIVMSG": self.cmd_privmsg,
                    "JOIN": self.cmd_join,
                    "PART": self.cmd_part,
                    "INVITE": self.cmd_invite,
                    "CHANLIST": self.cmd_chanlist,
                    }

            f = cmd_funcs.get(cmd, None)
            if f:
                f(user, obj)
            else:
                self.error(user, "command %s does not exist" % cmd)
        except AssertionError as e:
            self.error(user, "invalid message format")


    def cmd_user(self, user, obj):
        """Set username
        {
            "command": "USER",
            "args": ["username"]
        }
        """
        assert len(obj["args"]) == 1
        uname = obj["args"][0]
        assert isinstance(uname, str)

        # Username can only be set once
        if not user.has_username():
            user.set_username(uname)
        else:
            self.error(user, "can only set username once")

    def cmd_userlist(self, user, obj):
        """List all users on server
        {
            "command": "USERLIST",
            "args": []
        }
        """

        if user.has_username():
            args = [user.username for user in self.users]
            r = {
                    "user": user.username,
                    "command": "USERLIST",
                    "args": args
                    }
            self.send_obj(user, r)
        else:
            self.error(user, "must set username first")

    def cmd_msg(self, user, obj):
        """Send a message to a channel
        {
            "command": "MSG",
            "args": ["channel", "message text goes here"]
        }
        """
        assert len(obj["args"]) == 2
        chan = obj["args"][0]
        msg = obj["args"][1]
        assert isinstance(chan, str) and isinstance(msg, str)

        if user.has_username():
            r = {
                    "user": user.username,
                    "command": "MSG",
                    "args": [chan,msg]
                    }

            if user in self.channels[chan]:
                for member in self.channels[chan]:
                    if member.username != user.username:
                        self.send_obj(member, r)
        else:
            #TODO error out
            pass

    def cmd_privmsg(self, user, obj):
        """Send a private message to another user
        {
            "command": "PRIVMSG",
            "args": ["recvuser", "message text goes here"]
        }
        """
        #check validity of message
        assert len(obj["args"]) == 2
        recpt = obj["args"][0]
        msg = obj["args"][1]
        assert isinstance(recpt, str) and isinstance(msg, str)

        if user.has_username():
            r = {
                    "user": user.username,
                    "command": "PRIVMSG",
                    "args": [recpt, msg]
                    }
            for user in users:
                if user.username == recpt:
                    self.send_obj(user, r)
        else:
            #error out
            pass

    def cmd_join(self, user, obj):
        """Join user to a channel
        {
            "command": "JOIN",
            "args": ["channel1", "channel2", ...]
        }
        """
        for i in [isinstance(chan, str) for chan in obj["args"]]:
            assert i

        if user.has_username():
            for chan in obj["args"]:
                if not (chan in self.channels):
                    self.channels[chan] = [user]
                    #TODO send to all users in channel
                elif not (user in self.channels[chan]):
                    self.channels[chan].append(user)
                    #TODO send to all users in channel
                else:
                    self.error(user, "already in channel %s" % chan)
        else:
            #error out
            pass

    def cmd_part(self, user, obj):
        """Remove user from a channel
        {
            "command": "PART",
            "args": ["channel1", "channel2", ...]
        }
        """
        for i in [isinstance(chan, str) for chan in obj["args"]]:
            assert i

        if user.has_username():
            for chan in obj["args"]:
                if user in self.channels[chan]:
                    self.channels[chan].remove(user)
                    #TODO send to all users in channel
                else:
                    self.error(user, "not in channel %s" % chan)
        else:
            #error out
            pass

    def cmd_invite(self, user, obj):
        """Invite a user to channel
        {
            "command": "INVITE",
            "args": ["channel", "user1", "user2", ...]
        }
        """
        for i in [isinstance(chan, str) for chan in obj["args"]]:
            assert i
        assert len(obj["args"]) > 1
        chan = obj["args"][0]
        users = obj["args"][1:]

        if user.has_username():
            for u in users:
                r = {
                        "user": user.username,
                        "command": "INVITE",
                        "args": [chan]
                        }
                for i in self.users:
                    if i.username == u:
                        self.send_obj(r)

        else:
            #error out
            pass

    def cmd_chanlist(self, user, obj):
        """List all channels on server
        {
            "command": "CHANLIST",
            "args": []
        }
        """

        if user.has_username():
            #send list of channels to user
            r = {
                    "user": user.username,
                    "command": "CHANLIST",
                    "args": [i for i in self.channels]
                    }
            self.send_obj(user, r)
        else:
            #error out
            pass


    def error(self, user, msg):
        """Send an error object to a user with msg"""
        r = {"command": "ERROR", "args": [msg]}
        self.send_obj(user, r)

    def send_obj(self, user, obj):
        """Add obj to user's write queue"""

        conn = user.conn
        str_data = json.dumps(obj)
        byt_data = str_data.encode('utf-8') + u'\n'

        key = self.sel.get_key(conn)
        data = key.data

        # add message to the user data
        data["data"] = byt_data

        # add user to the write queue
        self.sel.modify(user.conn, selectors.EVENT_WRITE|selectors.EVENT_READ, data)

    def serve_forever(self):
        """Main event loop"""
        while True:
            # retreive a list of events that are ready to be processed
            # This line will block during the server's "resting state"
            # where no messages are being sent and nobody is connecting
            # or disconnecting
            events = self.sel.select()

            # There are 4 possible events in the list of events
            #
            # 1. User connects to the server
            #       # Server socket has EVENT_READ, and Something
            # 2. User disconnects from server
            #       # Server socket has EVENT_READ, and Something else
            # 3. User sends a message to the server
            #       # User socket has EVENT_READ
            # 4. Server sends a message to the user
            #       # User socket has EVENT_WRITE
            for key, mask in events:
                if mask == selectors.EVENT_WRITE:
                    # Event 4 - client ready to receive a message

                    # user data contains message
                    data = key.data["data"]

                    conn = key.fileobj
                    conn.sendall(data)

                    # Data has been written, remove user from the write queue
                    self.sel.modify(conn, selectors.EVENT_READ, data)

                elif key.data["newconn"]:
                    # Event 1 - new client connected to the server
                    # Event 2 - User disconnects from the server
                    # Right now only event 1 is handled, need a distinction between events
                    self.new_connection(key)

                else:
                    # Event 3 - client sent message to the server
                    self.recv_data(key)

#TODO: Timestamp objects when they come in or when they go out?

