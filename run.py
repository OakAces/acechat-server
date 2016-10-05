import acechat.server

addr = "localhost"
port = 9090

if __name__ == "__main__":
    serv = acechat.Server(addr, port)

    serv.serve_forever()
