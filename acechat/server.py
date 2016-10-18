import selectors
import json
import socket
import logging
import websockets
from json.decoder import JSONDecodeError
from acechat.user import User

class Server:
    def __init__(self):
        """Server class constructor"""
        self.logger = logging.getLogger("acechat.server")
        self.logger.info("Server starting")

        self.users = list()
        self.channels = dict()
        self.umap = dict()

    async def handler(self, ws, path):
        user = User(ws, path)
        self.users.append(user)
        while True:
            try:
                msg = await ws.recv()
            except websockets.exceptions.ConnectionClosed as e:
                self.logger.info("{} connection closed".format("User:{}".format(user.username) if user.username else "anonymous user"))
                return
            self.logger.info("<- {}".format(msg))
            obj = json.loads(msg)
            await self.process_cmd(user, obj)


    async def process_cmd(self, user, obj):
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
                await f(user, obj)
            else:
                await self.error(user, "command %s does not exist" % cmd)
        except AssertionError as e:
            await self.error(user, "invalid message format")


    async def cmd_user(self, user, obj):
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
        if user.has_username():
            await self.error(user, "can only set username once")
            return
        # Username must be unique
        for u in self.users:
            if u.username == uname:
                await self.error(user, "that username is already set")
                return

        # Username must be 10 characters or less
        if len(uname) > 10:
            await self.error(user, "username can only be 10 characters or less")
            return

        # Username should be alphanumeric with dashes or underscores
        valid = re.match('^[\w-_]+$', uname) is not None
        if not valid:
            await self.error(user, "username can only contain [a-zA-Z0-9_-]")
            return

        user.set_username(uname)
        r = {
            "user": uname,
            "command": "USER",
            "args": [uname]
        }
        await self.send_obj(user, r)

    async def cmd_userlist(self, user, obj):
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
            await self.send_obj(user, r)
        else:
            await self.error(user, "must set username first")

    async def cmd_msg(self, user, obj):
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
                    await self.send_obj(member, r)
        else:
            #TODO error out
            pass

    async def cmd_privmsg(self, user, obj):
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
                    await self.send_obj(user, r)
        else:
            #error out
            pass

    async def cmd_join(self, user, obj):
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
                    await self.error(user, "already in channel %s" % chan)
        else:
            #error out
            pass

    async def cmd_part(self, user, obj):
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
                    await self.error(user, "not in channel %s" % chan)
        else:
            #error out
            pass

    async def cmd_invite(self, user, obj):
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
                        await self.send_obj(r)

        else:
            #error out
            pass

    async def cmd_chanlist(self, user, obj):
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
            await self.send_obj(user, r)
        else:
            #error out
            pass


    async def error(self, user, msg):
        """Send an error object to a user with msg"""
        r = {"command": "ERROR", "args": [msg]}
        await self.send_obj(user, r)

    async def send_obj(self, user, obj):
        """Add obj to user's write queue"""
        conn = user.conn
        data = json.dumps(obj)
        self.logger.info("-> {}".format(data))
        await conn.send(data)

