#!/usr/bin/env python3

"""bjdns2_client.py

Usage:
  bjdns2_client.py (-s <BJDNS2_SERVER_ADDR>) (-i <BJDNS2_SERVER_IP>) [-d <DIRECT_DNS_SERVER>] [-b <LISTEN_IP_PORT>]

Examples:
  bjdns2_client.py -s "https://your.domain.name:your_port" -i "127.0.0.1" -d "119.29.29.29"

Options:
  -h --help             Show this screen
  -s BJDNS2_SERVER_ADDR bjdns2 server address
  -i BJDNS2_SERVER_IP   bjdns2 server ip
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
from bjdns2 import resp_from_json
from utils import (
    log,
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


class Bjdns2:
    def __init__(self, listen, bjdns2_url, bjdns2_ip):
        self.cache = Cache()

        ip, port_str = listen.split(':')
        self.server = DatagramServer((ip, int(port_str)), self.handle)
        self.session = requests.Session()

        url = urlparse(bjdns2_url).netloc
        self.bjdns2_host = url[:url.rfind(':')]
        self.bjdns2_ip = bjdns2_ip

    def query_by_https(self, host, cli_ip):
        url_template = bjdns2_url + '/?dn={}&ip={}'

        if host == self.bjdns2_host:
            return self.bjdns2_ip, 3600

        else:
            if is_private_ip(cli_ip):
                url = url_template.format(host, '')
            else:
                url = url_template.format(host, cli_ip)

            # try:
            r = self.session.get(url)
            # except Exception as e:
            #     log('Requests error:', e)
                # return '', 0
            # else:
            # if r.status_code == 200:
            result = json.loads(r.text)
            if result['Status'] == 0:
                self.cache.write(cli_ip, result)
                ip, ttl = resp_from_json(result)
                return ip, ttl
            else:
                return '', 0

    def query(self, data, host, cli_addr) -> bytes:
        src_ip, _ = cli_addr
        question = dict(name=host, type=1)
        resp = self.cache.select(src_ip, question)

        if resp:
            ip, ttl = resp_from_json(resp)
            log(cli_addr, '[cache]', host, ip, '(ttl:{})'.format(ttl))

        else:
            ip, ttl = self.query_by_https(host, src_ip)
            log(cli_addr, host, ip, '(ttl:{})'.format(ttl))

        if ip:
            return make_data(data, ip, ttl)
        else:
            return b''

    def handle(self, data, cli_addr):
        host, type = parse_query(data)
        if type == 1:
            try:
                resp = self.query(data, host, cli_addr)
            except Exception as e:
                log(e)
                resp = b''

        else:
            if host == self.bjdns2_host and type == 28:
                log(host, type)
                resp = data
            else:
                resp = query_by_udp(data)
            log(cli_addr, '[Type:{}]'.format(type), host)

        self.server.sendto(resp, cli_addr)

    def start(self):
        self.server.serve_forever()


if __name__ == '__main__':
    args = docopt(__doc__)

    # if args['-c']:
    #     cfg = config(args['-c']).get('client')
    #     bjdns2_url, bjdns2_ip = cfg['bjdns2_url'], cfg['bjdns2_ip']
    #     direct_dns_serv = cfg.get('direct_dns_server')
    #     listen = cfg.get("listen")
    # else:
    bjdns2_url, bjdns2_ip = args['-s'], args['-i']
    direct_dns_serv = args.get('-d')
    listen = args.get('-l')

    if not direct_dns_serv:
        direct_dns_serv = '119.29.29.29'
    if not listen:
        listen = '0.0.0.0:53'

    print('bjdns2 client start.')
    print('bjdns2 server:', bjdns2_url, bjdns2_ip)
    print('direct dns server:', direct_dns_serv)
    print('listen:', listen)
    print()
    bjdns2 = Bjdns2(listen, bjdns2_url, bjdns2_ip)
    bjdns2.start()
