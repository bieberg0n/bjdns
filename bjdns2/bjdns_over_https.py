import json
import time
import struct
import socket
from gevent import monkey, spawn
from flask import Flask, request
from gevent.wsgi import WSGIServer
# import aiohttp
# import aiosocks
# from aiosocks.connector import ProxyConnector, ProxyClientRequest
from utils import log
from cache import Cache
# from iscnip import iscnip_func
monkey.patch_all()
import requests


# iscnip = iscnip_func('ip.txt')
# PROXY_ADDRESS = '127.0.0.1'
# PROXY_PORT = 1080
cache = {}
app = Flask(__name__)


def whitelist():
    with open('whitelist.json') as f:
        txt = f.read()
    d = json.loads(txt)
    return d


wl = whitelist()


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


def cn_query(cn_host, client_ip):
    url_template = 'http://119.29.29.29/d?dn={}&ip={}'
    if is_private_ip(client_ip):
        url = url_template.format(cn_host, '')
    else:
        url = url_template.format(cn_host, client_ip)
    # async with aiohttp.ClientSession() as s:
    #     async with s.get(url) as r:
    #         resp = await r.text()
    #         return resp
    r = requests.get(url)
    result = r.text.split(';')[0]
    ip = result if result else ''
    ttl = 3600
    return ip, ttl


def resp_from_json(json_str):
    j = json.loads(json_str)
    if not j.get('Answer'):
        return '', 0
    else:
        for a in j['Answer']:
            if a.get('type') == 1:
                return a['data'], a['TTL']
        else:
            return '', 0


def foreign_query(foreign_host):
    url = 'https://dns.google.com/resolve?name={}'.format(foreign_host)
    s = requests.session()
    s.proxies = {'http': 'socks5://127.0.0.1:1080',
                 'https': 'socks5://127.0.0.1:1080'}
    r = s.get(url)
    return resp_from_json(r.text)


def query(host, cli_ip):
    if cli_ip == 'default':
        return foreign_query(host)
    else:
        return cn_query(host, cli_ip)


# def write_cache(cli_ip, host, ip, ttl):
#     if ip:
#         now = int(time.time())
#
#         if not cache.get(cli_ip):
#             cache[cli_ip] = dict()
#
#         cache[cli_ip][host] = dict(
#             ip=ip,
#             ttl=ttl,
#             querytime=now,
#         )
#     else:
#         return


def in_cache(cli_ip, host):
    # if cli_ip in cache and host in cache[cli_ip]:
    #     ttl = cache[cli_ip][host]['ttl']
    #     return host_timeout(cli_ip, host) <= ttl
    # else:
    #     return False
    pass


def is_cn_host(whitelist, host):
    h = list(reversed(host.split('.')))
    if h[0] == 'cn':
        return True
    elif len(h) > 1:
        return whitelist.get(h[0], {}).get(h[1]) == 1
    else:
        return False


def host_timeout(cli_ip, host):
    query_time = cache[cli_ip][host]['querytime']
    now = int(time.time())
    return now - query_time


def make_resp(ip, ttl):
    d = dict(
        data=ip,
        ttl=ttl,
    )
    return d


# def resp_from_cache(cli_ip, host):
#     ip, ttl = cache[cli_ip][host]['ip'], cache[cli_ip][host]['ttl']
#     current_ttl = ttl - host_timeout(cli_ip, host)
#     log(cli_ip, '[cache]', host, ip, '({})'.format(current_ttl))
#     return make_resp(ip, current_ttl)


def update_cache(host, cli_ip, cache):
    ip, ttl = query(host, cli_ip)
    if ip:
        cache.write(host, cli_ip, ip, ttl)
        log(host, 'reflush')
    return ip, ttl


def bjdns(host, cli_ip):
    _cli_ip = cli_ip
    if not is_cn_host(wl, host):
        cli_ip = 'default'
    ip, ttl = cache.select(host, cli_ip)
    if ip:
        t = cache.host_timeout(host, cli_ip)
        # ttl超时
        if t > ttl:
            resp = make_resp(ip, ttl)
            spawn(update_cache, host, cli_ip, cache)
        else:
            ttl = ttl - t
            resp = make_resp(ip, ttl)
        log(_cli_ip, host, '[cache]', ip, '(ttl: {})'.format(ttl))
        return resp
    else:
        ip, ttl = update_cache(host, cli_ip, cache)
        log(_cli_ip, host, ip, '({})'.format(ttl))
        return make_resp(ip, ttl)

    # if in_cache(cli_ip, host):
    #     resp = resp_from_cache(cli_ip, host)
    #     return resp
    # else:
    #     ip, ttl = query(host, cli_ip)
    #     write_cache(cli_ip, host, ip, ttl)
    #     log(cli_ip, host, ip, '({})'.format(ttl))
    #     return make_resp(ip, ttl)


@app.route('/', methods=['GET'])
def index():
    host = request.args.get('dn')
    cli_ip = request.args.get('ip')
    if host:
        cli_ip = cli_ip if cli_ip else request.remote_addr.split(':')[-1]
        resp = bjdns(host, cli_ip)
        return json.dumps(resp).encode()
    else:
        return 'BJDNS'


if __name__ == '__main__':
    cache = Cache()
    keyfile = ''
    certfile = ''
    if keyfile:
        WSGIServer(('', 53), app,
                   keyfile='ca.key',
                   certfile='ca.crt').serve_forever()
    else:
        WSGIServer(('', 5353), app).serve_forever()
