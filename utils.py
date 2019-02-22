import pprint
import time
import json
import struct
import socket
import config


def log(*args):
    # if len(args) == 1:
    #     pprint.pprint(*args)
    # else:
    print(time.strftime('%Y-%m-%d %H:%M:%S'), *args)


def dlog(*args):
    if config.debug:
        if len(args) == 1:
            pprint.pprint(*args)
        else:
            print(*args)


def resp_from_json(json_str: dict):
    j = json_str
    if not j.get('Answer'):
        return '', 0
    else:
        for a in j['Answer']:
            if a.get('type') == 1:
                return a['data'], a['TTL']
        else:
            return '', 0


def is_private_ip(ip):
    if ip == '' or ip == '1' or ip.startswith('127'):
        return True
    else:
        ip1 = 167772160
        ip2 = 2886729728
        ip3 = 3232235520
        binaryIp = socket.inet_aton(ip)
        numIp = struct.unpack('!L', binaryIp)[0]
        mark = 2**32-1
        ag = (mark << 16) & numIp
        if ip3 == ag:
            return True
        ag = mark << 20 & numIp
        if ip2 == ag:
            return True
        ag = (mark << 24) & numIp
        if ip1 == ag:
            return True
        return False


# def config(config_file):
#     with open(config_file) as f:
#         txt = f.read()
#     cfg = json.loads(txt)
#     return cfg
