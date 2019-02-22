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
    dlog,
    resp_from_json,
    is_private_ip,
    # config,
)
from cache import Cache
import config


app = Flask(__name__)


def whitelist():
    with open('whitelist.json') as f:
        txt = f.read()
    d = json.loads(txt)
    return d


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

    if [h for h in config.white_list if host.endswith(h)]:
        return True
    elif h[0] == 'cn':
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

    def cn_query(self, cn_host, client_ip) -> map:
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

    def foreign_query(self, name, dns_type) -> map:
        try:
            url = 'https://1.1.1.1/dns-query?ct=application/dns-json&name={}&type={}'
            r = self.s_proxy.get(url.format(name, dns_type), timeout=2)
            return json.loads(r.text)
        except Exception as e:
            log(e)
            url = 'https://8.8.8.8/resolve?name={}&type={}'
            r = self.s_proxy.get(url.format(name, dns_type), verify=False)
            return json.loads(r.text)

    def query(self, question: map, src_ip: str) -> map:
        name, dns_type = question['name'], question['type']
        if is_cn_host(self.wl, name):
            cn_flag = True
        else:
            cn_flag = False
            src_ip = '0.0.0.0'

        resp = self.cache.select(src_ip, question)
        dlog('resp:', resp)
        if not resp:
            if cn_flag and dns_type in (1, '1', 'A'):
                resp = self.cn_query(name, src_ip)
            else:
                resp = self.foreign_query(name, dns_type)

            if resp['Status'] == 0:
                dlog('src ip:', src_ip, 'resp:', resp)
                self.cache.write(src_ip, question, resp, b'')

            cache_flag = ''

        else:
            cache_flag = '[Cache] '

        return {
            'data': resp,
            'cache_flag': cache_flag,
            'cn_flag': '[cn] ' if cn_flag else '',
        }


class Bjdns:
    def __init__(self, by_proxy):
        self.query = Query(by_proxy)

    def bjdns(self, question: map, src_ip: str) -> map:
        # name, dns_type = question['name'], question['type']
        name = question['name']
        resp = self.query.query(question, src_ip)
        if resp['data']['Status'] == 0:
            data, ttl = resp_from_json(resp['data'])
            log('{0} {1} {2}{3}{4} (ttl: {5})'.format(src_ip, name, resp['cn_flag'], resp['cache_flag'], data, ttl))
        else:
            log('{} {}'.format(src_ip, name))

        return resp['data']


@app.route('/', methods=['GET'])
def index():
    host = request.args.get('dn')
    cli_ip = request.args.get('ip')
    dns_type = int(request.args.get('type', 1))

    if host:
        cli_ip = cli_ip if cli_ip else request.remote_addr.split(':')[-1]
        question = dict(name=host, type=dns_type)
        # try:
        resp = bjdns.bjdns(question, cli_ip)
        # except Exception as e:
        # log(e)
        # resp = make_resp('', '', 0)
        # finally:
        return json.dumps(resp).encode()
    else:
        return 'BJDNS'


bjdns = Bjdns(config.by_proxy)


if __name__ == '__main__':
    app.run(debug=True, port=5353)
