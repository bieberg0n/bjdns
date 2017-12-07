import pprint
import time
# from urllib.parse import urlparse
# from gevent import socket, ssl  # , monkey
# import geventsocks


# geventsocks.set_default_proxy('127.0.0.1', 1080)


def log(*args):
    if len(args) == 1:
        pprint.pprint(*args)
    else:
        print(time.strftime('%Y-%m-%d %H:%M:%S'), *args)
