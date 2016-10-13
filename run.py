import acechat.server
import websockets
import asyncio
import logging

logger = logging.getLogger('websockets.server')
logger.setLevel(logging.ERROR)
logger.addHandler(logging.StreamHandler())

addr = "localhost"
port = 9090

if __name__ == "__main__":
    serv = acechat.Server()

    start_server = websockets.serve(serv.handler, addr, port)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

