#!/usr/bin/env python3

"""bjdns3.py

Usage:
  bjdns3.py [--debug] [-d <DIRECT_DNS_SERVER>] [-l <LISTEN_IP_PORT>]

Examples:
  bjdns3.py -d "119.29.29.29"

Options:
  -h --help             Show this screen
  -d DIRECT_DNS_SERVER  dns server, be used when query type is not A
  -l LISTEN_IP_PORT     listen ip and port
  --debug               debug mode
"""

import re
import dnslib
from docopt import docopt
import json
from struct import (
    unpack,
    pack,
)
from gevent import (
    socket,
    monkey,
    # spawn,
)
# from urllib.parse import urlparse
from gevent.server import DatagramServer
from cache import Cache
import ipincn
from utils import (
    empty,
    info,
    resp_from_json,
    # is_private_ip,
    # config,
)
monkey.patch_all()
import requests


class CnHostChecker:
    def __init__(self):
        with open('whitelist.json') as f:
            txt = f.read()
        self.whitelist = json.loads(txt)

    def is_cn_host(self, host):
        h = [part for part in reversed(host.split('.')) if part]

        if h[0] == 'cn':
            return True
        elif len(h) > 1:
            return self.whitelist.get(h[0], {}).get(h[1]) == 1
        else:
            return False


def query_by_tcp(dns_ip, req_data):
    data = pack('>H', len(req_data)) + req_data

    s = socket.socket()
    # s.settimeout(2)
    s.connect((dns_ip, 53))
    s.sendall(data)
    # try:
    res = s.recv(2048)
    # except socket.timeout as e:
    #     info('query by tcp:', e)
    #     return b''

    s.close()
    if len(res) <= 2:
        return b''
    else:
        return res[2:]


def query_by_udp(dns_ip, raw_data):
    s = socket.socket(2, 2)
    # s.settimeout(2)
    s.sendto(raw_data, (dns_ip, 53))
    # try:
    res = s.recv(512)
    # except socket.timeout as e:
    #     info('query by udp:', e)
    #     return b''
    # else:
    return res


def ip_from_resp(resp):
    p = re.compile(b'\xc0.\x00\x01\x00\x01')

    try:
        res = p.split(resp)[1]
        ip_bytes = unpack('BBBB', res[6:10])
        ip = '.'.join([str(i) for i in ip_bytes])
    except IndexError as e:
        info('get ip from resp error:', e)
        ip = ''

    return ip


class DNSRequest:
    def __init__(self, raw_data, src_addr):
        self.raw_data = raw_data
        self.src = src_addr

        list_iter = iter(raw_data[13:])
        name = ''
        for bit in iter(lambda: next(list_iter), 0):
            name += '.' if bit < 32 else chr(bit)

        self.domain_name = name

        q_type = unpack('>H', raw_data[14+len(name):16+len(name)])
        self.type = q_type[0]
        self.question = dict(name=name, type=q_type)


class DNSResponse:
    def __init__(self, record=None, ip='', ttl=0, q_data=b''):
        if record:
            # self.ans = record
            self.raw = record.pack()

            rs = record.rr
            rs.extend(record.ar)
            # else:
            #     rs = record.ar

            # log(record.rr, record.ar)
            for r in rs:
                log(r.rdata, r.ttl)
                if r.rtype == 1:
                    self.ip = str(r.rdata)
                    self.ttl = r.ttl
                    return
            else:
                self.ip = ''
                self.ttl = 0

        else:
            self.ip = ip
            self.ttl = ttl
            self.raw = make_data(q_data, ip, ttl)


def make_data(data, ip, ttl):
    # data is request
    if ip:
        (id, flags, quests,
         answers, author, addition) = unpack('>HHHHHH', data[0:12])
        flags_new = 33152
        answers_new = 1
        res = pack('>HHHHHH', id, flags_new, quests,
                   answers_new, author, addition)

        res += data[12:]

        dns_answer = {
            'name': 49164,
            'type': 1,
            'classify': 1,
            'ttl': ttl,
            'datalength': 4
        }
        res += pack('>HHHLH',
                    dns_answer['name'],
                    dns_answer['type'],
                    dns_answer['classify'],
                    dns_answer['ttl'],
                    dns_answer['datalength'])

        ip = ip.split('.')
        ip_bytes = pack('BBBB', int(ip[0]), int(ip[1]),
                        int(ip[2]), int(ip[3]))

        res += ip_bytes
        return res

    else:
        return b''


class Bjdns:
    def __init__(self, listen, direct_dns_serv):
        self.cache = Cache()

        self.cn_dns = direct_dns_serv

        self.cn_checker = CnHostChecker()
        self.ip_in_cn = ipincn.ip_in_cn_gen()

        ip, port_str = listen.split(':')
        self.server = DatagramServer((ip, int(port_str)), self.handle)
        self.session = requests.Session()

    def query_by_cn(self, req: DNSRequest):
        raw_data = query_by_udp(self.cn_dns, req.raw_data)
        record = dnslib.DNSRecord.parse(raw_data)
        # ans = self.cn_resolver.query(req.domain_name)
        return DNSResponse(record=record)

    def query_by_oversea(self, req:DNSRequest):
        url = 'https://1.1.1.1/dns-query?ct=application/dns-json&name={}&type=1'.format(req.domain_name)
        src_ip = req.src[0]
        try:
            r = self.session.get(url, timeout=5)
            result = json.loads(r.text)
            if result['Status'] == 0:
                ip, ttl = resp_from_json(result)
            else:
                ip, ttl = '', 0

            resp = DNSResponse(ip=ip, ttl=ttl, q_data=req.raw_data)

        except Exception as e:
            info(e)
            record = query_by_tcp('208.67.220.220', req.raw_data)
            resp = DNSResponse(record=record)
            # self.cache.write(src_ip, req.question, None, resp.raw)

        self.cache.write(src_ip, req.question, resp)
        return resp

    def _query(self, req: DNSRequest) -> DNSResponse:
        src_ip = req.src[0]
        resp = self.query_by_cn(req)

        if self.cn_checker.is_cn_host(req.domain_name) or self.ip_in_cn(resp.ip):
            self.cache.write(src_ip, req.question, resp)
            return resp

        else:
            return self.query_by_oversea(req)

    def query(self, req: DNSRequest) -> bytes:
        src_ip, _ = req.src
        cache_resp = self.cache.select(src_ip, req.question)

        if cache_resp:
            resp = DNSResponse(record=dnslib.DNSRecord.parse(cache_resp))
            info(req.src, '[cache]', req.domain_name, resp.ip, '(ttl:{})'.format(resp.ttl))
            return make_data(req.raw_data, resp.ip, resp.ttl)

        elif req.type == 1:
            resp = self._query(req)
            info(req.src, req.domain_name, resp.ip, '(ttl:{})'.format(resp.ttl))
            return resp.raw

        else:
            info(req.src, '[Type:{}]'.format(req.type), req.domain_name)
            resp = self.query_by_cn(req)
            self.cache.write(src_ip, req.question, resp)
            return resp.raw

    def handle(self, data, cli_addr):
        req = DNSRequest(data, cli_addr)

        # try:
        resp_data = self.query(req)
        # except Exception as e:
        #     info(e)
        #     resp = b''

        self.server.sendto(resp_data, cli_addr)

    def start(self):
        self.server.serve_forever()


if __name__ == '__main__':
    args = docopt(__doc__)

    direct_dns_serv = args.get('-d')
    listen = args.get('-l')
    debug_mode = args.get('--debug')

    if debug_mode:
        log = info
    else:
        log = empty

    if not direct_dns_serv:
        direct_dns_serv = '223.5.5.5'
    if not listen:
        listen = '0.0.0.0:53'

    info('bjdns3 start.')
    info('direct dns server:', direct_dns_serv)
    info('listen:', listen)
    bjdns = Bjdns(listen, direct_dns_serv)
    bjdns.start()
