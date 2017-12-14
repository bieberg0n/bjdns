#!/usr/bin/env python3

import json
# import struct
# import socket
from gevent import (
    # socket,
    monkey,
    spawn,
    ssl,
)
from gevent.wsgi import WSGIServer
from flask import (
    Flask,
    request,
)
from utils import (
    log,
    is_private_ip,
)
from cache import Cache
from bjdns2_config import config
monkey.patch_all()
import requests


app = Flask(__name__)


def whitelist():
    with open('whitelist.json') as f:
        txt = f.read()
    d = json.loads(txt)
    return d


wl = whitelist()


def cn_query(cn_host, client_ip):
    url_template = 'http://119.29.29.29/d?dn={}&ip={}'
    if is_private_ip(client_ip):
        url = url_template.format(cn_host, '')
    else:
        url = url_template.format(cn_host, client_ip)
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


def is_cn_host(whitelist, host):
    h = list(reversed(host.split('.')))
    if h[0] == 'cn':
        return True
    elif len(h) > 1:
        return whitelist.get(h[0], {}).get(h[1]) == 1
    else:
        return False


def make_resp(ip, ttl):
    d = dict(
        data=ip,
        ttl=ttl,
    )
    return d


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
        t = cache.timeout(host, cli_ip)
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
        log(_cli_ip, host, ip, '(ttl: {})'.format(ttl))
        return make_resp(ip, ttl)


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
    keyfile = config.keyfile
    certfile = config.keyfile
    if keyfile:
        WSGIServer(
            ('', 5353), app,
            keyfile=keyfile,
            certfile=certfile,
            ssl_version=ssl.PROTOCOL_TLSv1_2
        ).serve_forever()
    else:
        WSGIServer(('', 5353), app).serve_forever()
