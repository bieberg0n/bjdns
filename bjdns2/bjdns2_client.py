#!/usr/bin/env python3

"""bjdns2_client.py

Usage:
  bjdns2_client.py (-s <BJDNS2_SERVER_ADDR>) (-i <BJDNS2_SERVER_IP>)
  bjdns2_client.py (-c <CONFIG_FILE>)


Examples:
  bjdns2_client.py -s "https://your.domain.name:your_port" -i "127.0.0.1"
  bjdns2_client.py -c "config.json"

Options:
  -h --help             Show this screen
  -s BJDNS2_SERVER_ADDR bjdns2 server address
  -i BJDNS2_SERVER_IP   bjdns2 server ip
  -c CONFIG_FILE        path to config file
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
    spawn,
)
from gevent.server import DatagramServer
from cache import Cache
from utils import (
    log,
    is_private_ip,
    config,
)
monkey.patch_all()
import requests


def query_by_udp(data):
    s = socket.socket(2, 2)
    s.settimeout(2)
    # s.sendto(data, ('114.114.114.114', 53))
    # s.sendto(data, ('119.29.29.29', 53))
    s.sendto(data, ('223.5.5.5', 53))
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
    # log('type,', type)
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
    # try:
    ip_bytes = pack('BBBB', int(ip[0]), int(ip[1]),
                    int(ip[2]), int(ip[3]))
    # except ValueError as e:
    #     print(e, cache)

    res += ip_bytes
    return res


class Bjdns2:
    def __init__(self, bjdns2_host, bjdns2_ip):
        self.cache = Cache()
        self.server = DatagramServer(('0.0.0.0', 53), self.handle)
        self.session = requests.Session()
        self.bjdns2_host = bjdns2_host
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

            try:
                r = self.session.get(url)
            except Exception as e:
                log('Requests error:', e)
                return '', 0
            else:
                if r.status_code == 200:
                    result = json.loads(r.text)
                    ip = result.get('data') if result else ''
                    ttl = result.get('ttl')
                    return ip, ttl
                else:
                    return '', 0

    def update_cache(self, host, cli_ip):
        ip, ttl = self.query_by_https(host, cli_ip)
        if ip:
            self.cache.write(host, cli_ip, ip, ttl)
            log(host, 'reflush')
        return ip, ttl

    def query(self, data, cache, host, cli_addr):
        # mode = 'default'
        cli_ip = cli_addr[0]
        ip, ttl = cache.select(host, cli_ip)
        if ip:
            # 命中缓存
            timeout = cache.timeout(host, cli_ip)
            if timeout > ttl:
                # 超时更新缓存
                spawn(self.update_cache, host, cli_ip)
            else:
                ttl = ttl - timeout
            log(cli_addr, '[cache]', host, ip, '(ttl:{})'.format(ttl))
        else:
            # 未命中，更新缓存
            ip, ttl = self.update_cache(host, cli_ip)
            log(cli_addr, host, ip, '(ttl:{})'.format(ttl))

        if ip:
            resp = make_data(data, ip, ttl)
        else:
            resp = b''

        return resp

    def handle(self, data, cli_addr):
        host, type = parse_query(data)
        if type == 1:
            resp = self.query(data, self.cache, host, cli_addr)
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

    if args['-c']:
        cfg = config(args['-c']).get('client')
        bjdns2_url, bjdns2_ip = cfg['bjdns2_url'], cfg['bjdns2_ip']
    else:
        bjdns2_url, bjdns2_ip = args['-s'], args['-i']
    bjdns2_host = bjdns2_url.split('/')[-1].split(':')[0]

    print('bjdns2 client start.\nbjdns2 server:', bjdns2_url, bjdns2_ip, '\n')
    bjdns2 = Bjdns2(bjdns2_host, bjdns2_ip)
    bjdns2.start()
