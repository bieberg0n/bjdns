import json
from struct import unpack, pack
from gevent import socket, monkey
from gevent.server import DatagramServer
from utils import log
from cache import Cache
monkey.patch_all()
import requests


def query_by_https(host):
    if host == 'g.bjong.me':
        return '121.42.185.92', 3600
    else:
        url = 'https://g.bjong.me:5353/?dn={}'.format(host)
        r = requests.get(url)
        # log(r.text)
        if r.status_code == 200:
            result = json.loads(r.text)
            ip = result.get('data') if result else ''
            ttl = result.get('ttl')
            return ip, ttl
        else:
            return '', 0


def query_by_udp(data):
    s = socket.socket()
    # s.connect(('114.114.114.114', 53))
    s.sendto(data, ('114.114.114.114', 53))
    res = s.recv(512)
    # if len(res) <= 2:
    #     s.close()
    #     return b''
    # else:
    #     s.close()
    #     return res[2:]
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
    # try:
    ip_bytes = pack('BBBB', int(ip[0]), int(ip[1]),
                    int(ip[2]), int(ip[3]))
    # except ValueError as e:
    #     print(e, cache)

    res += ip_bytes
    return res


def in_cache(cache, host):
    mode = 'default'
    ip, ttl = cache.select(host, mode)
    if ip:
        timeout = cache.host_timeout(host, mode)
        if timeout < ttl:
            return ip, ttl - timeout
        else:
            return '', 0
    else:
        return '', 0


def query(data, cache, host, cli_addr):
    mode = 'default'
    ip, ttl = in_cache(cache, host)
    if ip:
        resp = make_data(data, ip, ttl)
        log(cli_addr, '[cache]', host, ip, '(ttl:{})'.format(ttl))
    else:
        ip, ttl = query_by_https(host)
        if ip:
            cache.write(host, mode, ip, ttl)
            resp = make_data(data, ip, ttl)
            log(cli_addr, host, ip, '(ttl:{})'.format(ttl))
        else:
            resp = b''
            log(cli_addr, host)

    return resp


def handle_func():
    # cache = {}
    cache = Cache()

    def handle(data, cli_addr):
        host, type = parse_query(data)
        if type == 0:
            # log(type)
            resp = query_by_udp(data)
            log(cli_addr, '(type is not A)', host)
        else:
            resp = query(data, cache, host, cli_addr)
        server.sendto(resp, cli_addr)

    return handle


def bjdns():
    global server
    handle = handle_func()
    server = DatagramServer(('127.0.0.1', 53), handle)
    server.serve_forever()


if __name__ == '__main__':
    # log(query_by_https('baidu.com'))
    bjdns()
