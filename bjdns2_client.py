#!/usr/bin/env python3

"""bjdns2_client.py

Usage:
  bjdns2_client.py (-s <BJDNS2_SERVER_ADDR>) [-d <DIRECT_DNS_SERVER>] [-b <LISTEN_IP_PORT>]

Examples:
  bjdns2_client.py -s "https://your.domain.name:your_port" -d "119.29.29.29"

Options:
  -h --help             Show this screen
  -s BJDNS2_SERVER_ADDR bjdns2 server address
  -d DIRECT_DNS_SERVER  dns server, be used when query type is not A
  -b LISTEN_IP_PORT     listen ip and port
"""

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
from urllib.parse import urlparse
from gevent.server import DatagramServer
from cache import Cache
from utils import (
    log,
    resp_from_json,
    is_private_ip,
    # config,
)
monkey.patch_all()
import requests


def query_by_udp(data):
    s = socket.socket(2, 2)
    s.settimeout(2)
    s.sendto(data, (direct_dns_serv, 53))
    try:
        res = s.recv(512)
    except socket.timeout as e:
        log('query special type:', e)
        return b''
    else:
        return res


def parse_query(data):
    list_iter = iter(data[13:])
    name = ''
    for bit in iter(lambda: next(list_iter), 0):
        name += '.' if bit < 32 else chr(bit)

    type = unpack('>H', data[14+len(name):16+len(name)])
    type = type[0]
    return name, type


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


class Bjdns2:
    def __init__(self, listen, bjdns2_url):
        self.cache = Cache()

        ip, port_str = listen.split(':')
        self.server = DatagramServer((ip, int(port_str)), self.handle)
        self.session = requests.Session()

        url = urlparse(bjdns2_url).netloc
        self.bjdns2_host = url[:url.rfind(':')]

    def query_by_https(self, host, cli_ip):
        url_template = bjdns2_url + '/?dn={}&ip={}'

        if is_private_ip(cli_ip):
            url = url_template.format(host, '')
        else:
            url = url_template.format(host, cli_ip)

        r = self.session.get(url)
        result = json.loads(r.text)
        if result['Status'] == 0:
            self.cache.write(cli_ip, result['Question'][0], result, None)
            ip, ttl = resp_from_json(result)
            return ip, ttl
        else:
            return '', 0

    def query(self, data, host, q_type, cli_addr) -> bytes:
        src_ip, _ = cli_addr
        question = dict(name=host, type=q_type)
        cache_resp = self.cache.select(src_ip, question)

        if cache_resp:
            if host == self.bjdns2_host or q_type != 1:
                resp = data[:2] + cache_resp
                log(cli_addr, '[cache]', '[Type:{}]'.format(q_type), host)
            else:
                ip, ttl = resp_from_json(cache_resp)
                log(cli_addr, '[cache]', host, ip, '(ttl:{})'.format(ttl))
                resp = make_data(data, ip, ttl)

        else:
            if host == self.bjdns2_host or q_type != 1:
                resp = query_by_udp(data)
                self.cache.write(src_ip, question, None, resp[2:])
                log(cli_addr, '[Type:{}]'.format(q_type), host)

            else:
                ip, ttl = self.query_by_https(host, src_ip)
                log(cli_addr, host, ip, '(ttl:{})'.format(ttl))
                resp = make_data(data, ip, ttl)

        return resp

    def handle(self, data, cli_addr):
        host, q_type = parse_query(data)

        try:
            resp = self.query(data, host, q_type, cli_addr)
        except Exception as e:
            log(e)
            resp = b''

        self.server.sendto(resp, cli_addr)

    def start(self):
        self.server.serve_forever()


if __name__ == '__main__':
    args = docopt(__doc__)

    bjdns2_url = args['-s']
    direct_dns_serv = args.get('-d')
    listen = args.get('-l')

    if not direct_dns_serv:
        direct_dns_serv = '119.29.29.29'
    if not listen:
        listen = '0.0.0.0:53'

    log('bjdns2 client start.')
    log('bjdns2 server:', bjdns2_url)
    log('direct dns server:', direct_dns_serv)
    log('listen:', listen)
    bjdns2 = Bjdns2(listen, bjdns2_url)
    bjdns2.start()
