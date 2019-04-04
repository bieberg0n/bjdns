#!/usr/bin/env python3

import json
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
    CnHostChecker,
)
from cache import Cache
import ipincn
import config


app = Flask(__name__)


def make_resp_data(name, ip, ttl):
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


def make_resp(data, cache_flag, cn_flag):
    cache_msg = '[Cache] ' if cache_flag else ''
    cn_msg = '[cn] ' if cn_flag else ''

    return {
        'data': data,
        'cache_flag': cache_msg,
        'cn_flag': cn_msg,
    }


class Query:
    def __init__(self, by_proxy):
        self.cache = Cache()
        self.cn_host_checker = CnHostChecker()
        self.ip_in_cn = ipincn.ip_in_cn_gen()
        self.s_cn = requests.session()
        self.s_proxy = requests.session()
        if by_proxy:
            self.s_proxy.proxies = {
            'http': 'socks5h://127.0.0.1:1080',
            'https': 'socks5h://127.0.0.1:1080'
            }

    def cn_query_ip(self, cn_host, client_ip) -> str:
        dlog('query ip to cn')
        url_template = 'http://119.29.29.29/d?dn={}&ip={}'
        if is_private_ip(client_ip):
            url = url_template.format(cn_host, '')
        else:
            url = url_template.format(cn_host, client_ip)
        r = self.s_cn.get(url)
        result = r.text.split(';')[0]

        if result:
            return result
        else:
            return ''

    def cn_query(self, cn_host, client_ip) -> map:
        dlog('query to cn')
        ip = self.cn_query_ip(cn_host, client_ip)
        ttl = 3600
        return make_resp_data(cn_host, ip, ttl)

    def query_google(self, name, dns_type, client_ip=''):
        dlog('query to google')
        url = 'https://8.8.8.8/resolve?name={}&type={}'.format(name, dns_type)
        if client_ip:
            url = url + '&edns_client_subnet=' + client_ip
        dlog('url:', url)
        r = self.s_proxy.get(url)
        return json.loads(r.text)

    def foreign_query(self, name, dns_type) -> map:
        dlog('query to cloudflare')
        try:
            url = 'https://1.1.1.1/dns-query?ct=application/dns-json&name={}&type={}'
            r = self.s_proxy.get(url.format(name, dns_type), timeout=2)
            return json.loads(r.text)
        except Exception as e:
            log(e)
            return self.query_google(self, name, dns_type)

    def save(self, src_ip, question, data):
        if data['Status'] == 0:
            dlog('src ip:', src_ip, 'data:', data)
            self.cache.write(src_ip, question, data, b'')

    def query(self, question: map, src_ip: str) -> map:
        name, dns_type = question['name'], question['type']

        data = self.cache.select(src_ip, question)
        dlog('resp:', data)
        if data:
            return make_resp(data, cache_flag=True, cn_flag=False)

        elif self.cn_host_checker.is_cn_host(name) and dns_type in (1, '1', 'A'):
            try:
                data = self.cn_query(name, src_ip)
            except Exception as e:
                log('cn query error:', e)
                data = self.query_google(name, dns_type, src_ip)
            finally:
                resp = make_resp(data, cache_flag=False, cn_flag=True)

        else:
            ip = self.cn_query_ip(name, src_ip)
            dlog('IP:', ip)
            is_cn_ip = self.ip_in_cn(ip) if ip else False
            if (not ip) or is_cn_ip:
                data = make_resp_data(name, ip, 3600)
                resp = make_resp(data, cache_flag=False, cn_flag=True)
            else:
                data = self.foreign_query(name, dns_type)
                resp = make_resp(data, cache_flag=False, cn_flag=False)

        self.save(src_ip, question, data)
        return resp


class Bjdns:
    def __init__(self, by_proxy):
        self.query = Query(by_proxy)

    def bjdns(self, question: map, src_ip: str) -> map:
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
    cli_ips = [
        request.args.get('ip'),
        request.headers.get('X-Forwarded-For'),
        request.remote_addr.split(':')[-1]
    ]
    cli_ip, *_ = [ip for ip in cli_ips if ip]
    dns_type = int(request.args.get('type', 1))

    if host:
        question = dict(name=host, type=dns_type)
        resp = bjdns.bjdns(question, cli_ip)
        return json.dumps(resp).encode()
    else:
        return 'BJDNS'


bjdns = Bjdns(config.by_proxy)


if __name__ == '__main__':
    app.run(debug=True, port=5353)
