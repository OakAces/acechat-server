import json
#import threading (hasn't been used yet, so I just commented it out)
import time
import selectors
import socket

sel = selectors.DefaultSelector()
channels = dict()
users = dict()
'''This file holds all server information needed for AceChat'''

class Channel():
    '''the channel users speak in'''
    def __init__(self, name):
        '''creates the list of users in the channel'''
        self.users = list()
        self.name = name

    def send(self, obj):
        '''sends an object to all users in the channel'''
        for u in self.users:
            u.send(obj)

    def part(self, user):
        '''removes user from channel'''
        self.users.remove(user)
        r = {"command": "PART",
                "args": [user.username]
        }
        for u in self.users:
            u.send(r)

class User():
    '''The class for the user'''
    def __init__(self, sock):
        '''creates the default user obj with nothing'''
        self.username = None
        self.channels = dict()
        self.data = bytes()
        self.sock = sock

    def send(self, obj):
        '''sends a timestamped message in JSON'''
        obj["timestamp"] = time.time()
        data = json.dumps(obj) + "\n"
        data = data.encode("utf-8")
        self.sock.send(data)

    def read(self, conn, mask):
        '''
        reads data and:
            if username declared, error
            if username not declared, error
            else part from all channels and close connection
        '''
        data = conn.recv(1000)
        if data:
            self.data = self.data + data
            print('received: ', repr(data))
            for line in self.data.splitlines:
                line = line.decode("utf-8")
                obj = json.loads(line)
                if obj["command"] == "USER" and self.username:
                    r = {
                            "command": "ERROR",
                            "args": ["already declared a username"]
                            }
                    self.send(r)
                elif obj["command"] != "USER" and not self.username:
                    r = {
                            "command": "ERROR",
                            "args": ["must declare a username"]
                            }
                    self.send(r)
        else:
            print('closing', conn)
            for chan in self.channels:
                self.channels[chan].part(self)
            del users[self.username]
            sel.unregister(conn)
            conn.close()

    def cmd_msg(self, obj):
        '''
        send a message in JSON with the arg format {channel, utf8Text}
        if channel doesn't exist, error
        if any args are missing, error
        else send the message
        '''
        args = obj["args"]
        if len(args) != 2:
            r = {"command": "ERROR",
                    "args": ["must specify channel and message text"]}
            self.send(r)
        elif not args[0] in channels:
            r = {"command": "ERROR",
                    "args": ["that channel doesn't exist"]
                    }
            self.send(r)
        else:
            obj["user"] = self.username
            channels[args[0]].send(obj)

    def cmd_privmsg(self, obj):
        '''
        send a DM in JSON with the arg format {channel, utf8Text}
        if user doesn't exist, error
        if any args are missing, error
        else send the message
        '''
        args = obj["args"]
        if len(args) != 2:
            r = {"command": "ERROR",
                    "args": ["must specify username and message text"]}
            self.send(r)
        elif not args[0] in users:
            r = {"command": "ERROR",
                    "args": ["that user doesn't exist"]}
            self.send(r)
        else:
            obj["user"] = self.username
            users[args[0]].send(obj)

    def cmd_user(self, obj):
        '''
        sets username
        if username not specified in command, error
        '''
        #TODO if user already exists, different error
        args = obj["args"]
        if len(args) != 1:
            r = {"command": "ERROR",
                    "args": ["must specify username"]}
            self.send(r)
        self.username = args[0]
        users[args[0]] = self

    def cmd_invite(self, obj):
        '''
        invite users to channel
        '''
        args = obj["args"]
        if len(args) < 2:
            r = {"command": "ERROR",
                    "args": ["must specify channel and at least one user"]}
        elif not args[0] in self.channels:
            r = {"command": "ERROR",
                    "args": ["must be in channel to invite user to it"]}
        else:
            chan = args[0]
            for u in args[1:]
                r = {
                    "user": self.username,
                    "command": "INVITE",
                    "args": [chan]
                }
                try:
                    users[u].send(r)
                except KeyError e:
                    print("cannot invite non-existing user", e)

    def cmd_chanlist(self, obj):
        '''sends the list of channels to users'''
        obj["args"] = list(channels.keys())
        self.send(obj)


def new_connection(sock, mask):
    '''connects the user'''
    conn, addr = sock.accept()  # Should be ready
    print('accepted', conn, 'from', addr)
    conn.setblocking(False)
    user = User(conn)
    sel.register(conn, selectors.EVENT_READ, user.read)


def main():
    sock = socket.socket()
    sock.bind(("localhost", 9090))
    sock.listen(5)
    print("listening")
    sock.setblocking(False)
    print('registering')
    sel.register(sock, selectors.EVENT_READ, new_connection)

    while True:
        events = sel.select()
        for key, mask in events:
            cb = key.data
            cb(key.fileobj, mask)

if __name__ == "__main__":
    main()
