import acechat.server
import websockets
import asyncio
import logging

logging.basicConfig(level=logging.INFO)

wslogger = logging.getLogger('websockets.server')
wslogger.setLevel(logging.INFO)
wslogger.addHandler(logging.StreamHandler())

addr = "localhost"
port = 9090

if __name__ == "__main__":
    serv = acechat.Server()

    start_server = websockets.serve(serv.handler, addr, port)

    print("Listening on http://{}:{}".format(addr, port))
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

