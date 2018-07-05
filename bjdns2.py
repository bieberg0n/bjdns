#!/usr/bin/env python3

import json
# from gevent import (
#     monkey,
#     ssl,
# )
# monkey.patch_all()
# from gevent.pywsgi import WSGIServer
import requests
from flask import (
    Flask,
    request,
)
from utils import (
    log,
    is_private_ip,
    config,
)
from cache import Cache


app = Flask(__name__)


def whitelist():
    with open('whitelist.json') as f:
        txt = f.read()
    d = json.loads(txt)
    return d


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


def make_resp(name, ip, ttl):
    if not name.endswith('.'):
        name += '.'

    resp = {
        "TC": False,
        "RD": True,
        "RA": True,
        "AD": True,
        "CD": False,
        "Question": [
            {
                "name": name,
                "type": 1
            }
        ],
    }
    if ip:
        resp['Status'] = 0
        resp["Answer"] = [
            {
                "name": name,
                "type": 1,
                "TTL": ttl,
                "data": ip
            }
        ]
    else:
        resp['Status'] = 2
    return resp


def is_cn_host(whitelist, host):
    h = [part for part in reversed(host.split('.')) if part]
    if h[0] == 'cn':
        return True
    elif len(h) > 1:
        return whitelist.get(h[0], {}).get(h[1]) == 1
    else:
        return False


class Query:
    def __init__(self, by_proxy):
        self.cache = Cache()
        self.wl = whitelist()
        self.s_cn = requests.session()
        self.s_proxy = requests.session()
        if by_proxy:
            self.s_proxy.proxies = {
            'http': 'socks5h://127.0.0.1:1080',
            'https': 'socks5h://127.0.0.1:1080'
            }

    def _cn_query(self, cn_host, client_ip) -> map:
        url_template = 'http://119.29.29.29/d?dn={}&ip={}'
        if is_private_ip(client_ip):
            url = url_template.format(cn_host, '')
        else:
            url = url_template.format(cn_host, client_ip)
        r = self.s_cn.get(url)
        result = r.text.split(';')[0]
        ip = result if result else ''
        ttl = 3600
        return make_resp(cn_host, ip, ttl)

    def _foreign_query(self, name, type) -> map:
        url = 'https://1.1.1.1/dns-query?ct=application/dns-json&name={}&type={}'
        r = self.s_proxy.get(url.format(name, type))
        return json.loads(r.text)

    def query(self, question: map, src_ip: str) -> map:
        name, dns_type = question['name'], question['type']
        if is_cn_host(self.wl, name):
            cn_flag = True
        else:
            cn_flag = False
            src_ip = '0.0.0.0'

        resp = self.cache.select(src_ip, question)
        if not resp:
            if cn_flag and dns_type in (1, '1', 'A'):
                resp = self._cn_query(name, src_ip)
            else:
                resp = self._foreign_query(name, dns_type)

            if resp['Status'] == 0:
                self.cache.write(src_ip, resp)

            cache_flag = ''

        else:
            cache_flag = '[Cache] '

        return resp, cache_flag


class Bjdns:
    def __init__(self, by_proxy):
        self.query = Query(by_proxy)

    def bjdns(self, question: map, src_ip: str) -> map:
        name, dns_type = question['name'], question['type']
        resp, cache_flag = self.query.query(question, src_ip)
        if resp['Status'] == 0:
            data, ttl = resp_from_json(resp)
            log('{0} {1} {2}{3} (ttl: {4})'.format(src_ip, name, cache_flag, data, ttl))
        else:
            log('{} {}'.format(src_ip, name))

        return resp


@app.route('/', methods=['GET'])
def index():
    host = request.args.get('dn')
    cli_ip = request.args.get('ip')
    dns_type = int(request.args.get('type', 1))

    if host:
        cli_ip = cli_ip if cli_ip else request.remote_addr.split(':')[-1]
        question = dict(name=host, type=dns_type)
        try:
            resp = bjdns.bjdns(question, cli_ip)
        except Exception as e:
            log(e)
            resp = make_resp('', '', 0)
        finally:
            return json.dumps(resp).encode()
    else:
        return 'BJDNS'


cfg = config('config.json').get('server')
by_proxy = cfg['proxy']
bjdns = Bjdns(by_proxy)


if __name__ == '__main__':
    log(cfg)
    keyfile = cfg['keyfile']
    certfile = cfg['certfile']


    # if keyfile:
    #     WSGIServer(
    #         (cfg['listen_ip'], cfg['listen_port']),
    #         app,
    #         keyfile=keyfile,
    #         certfile=certfile,
    #         ssl_version=ssl.PROTOCOL_TLSv1_2
    #     ).serve_forever()
    # else:
    #     WSGIServer(
    #         (cfg['listen_ip'], cfg['listen_port']),
    #         app,
    #     ).serve_forever()
    app.run(debug=True)
