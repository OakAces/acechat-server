import json
import threading
import time
import selectors
import socket

sel = selectors.DefaultSelector()
channels = dict()
users = dict()

class Channel():
    def __init__(self):
        self.users = list()

    def send(self, obj):
        for u in self.users:
            u.send(obj)

    def part(self, user):
        self.users.remove(user)
        for u in self.users:
            #TODO notify users of part
            pass


class User():

    def __init__(self, sock):
        self.username = None
        self.channels = list()
        self.data = bytes()
        self.sock = sock

    def send(self, obj):
        obj["timestamp"] = time.time()
        data = json.dumps(obj)
        data = data.encode("utf-8")
        self.sock.send(data)

    def read(self, conn, mask):
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
                chan.part(self)
            del users[self.username]
            sel.unregister(conn)
            conn.close()

    def cmd_msg(self, obj):
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
        args = obj["args"]
        if len(args) != 1:
            r = {"command": "ERROR",
                    "args": ["must specify username"]}
            self.send(r)
        users[args[0]] = self




def new_connection(sock, mask):
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
        for key,mask in events:
            cb = key.data
            cb(key.fileobj, mask)

if __name__ == "__main__":
    main()
