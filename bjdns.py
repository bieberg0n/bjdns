#!/usr/bin/env python3
# coding=utf-8

# copyright 2016 bjong

import sys
import os
import time
import json
import re
import struct
import pprint
from struct import pack, unpack
from gevent.server import DatagramServer
from gevent import socket, monkey
import geventsocks
monkey.patch_all()
import requests


s = requests.session()


def log(*args):
    if len(args) == 1:
        pprint.pprint(*args)
    else:
        print(time.strftime('%Y-%m-%d %H:%M:%S'), *args)


def inlist(name, dict_):
    name = name.split('.')
    name.reverse()
    for i in range(1, len(name)+1):
        name_ = list(reversed([name[j] for j in range(i)]))
        name_ = '.' + '.'.join(name_)
        if dict_.get(name_):
            return True
    else:
        return False


def is_private_ip(ip):
    if ip.startswith('127'):
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


def get_dns_by_http(domain_name, client_ip):
    url_template = 'http://119.29.29.29/d?dn={}&ip={}'
    # log('*** debug url', url_template.format(domain_name, ''))
    if is_private_ip(client_ip):
        r = s.get(url_template.format(domain_name, ''))
    else:
        r = s.get(url_template.format(domain_name, client_ip))
    result = r.text.split(';')[0]
    ip = result if result else ''
    # log('*** debug r', r.text)
    ttl = 3600
    return ip, ttl


def get_dns_by_tcp(query_data, dns_server, by_socks=False):
    data = pack('>H', len(query_data)) + query_data

    if by_socks:
        s = socket.socket()
        geventsocks.connect(s, dns_server)
    else:
        s = socket.socket()
        s.connect(dns_server)

    s.send(data)
    res = s.recv(512)
    if len(res) <= 2:
        s.close()
        return b''
    else:
        s.close()
        return res[2:]


def get_dns(query_data, domain_name, client_ip,
            dns_server, by_socks=False, by_httpdns=False):
    if by_socks or not by_httpdns:
        resp = get_dns_by_tcp(query_data, dns_server, by_socks)
        ip = get_ip_from_resp(resp, len(query_data))
        ttl = 3600
    else:
        ip, ttl = get_dns_by_http(domain_name, client_ip)
        resp = make_data(query_data, ip, ttl) if ip else b''

    return (resp, ip, ttl)


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


def get_ip_from_resp(res, data_len):
    ip = ''
    p = re.compile(b'\xc0.\x00\x01\x00\x01')
    try:
        res = p.split(res)[1]
        ip_bytes = unpack('BBBB', res[6:10])
        ip = '.'.join([str(i) for i in ip_bytes])
    except IndexError as e:
        pass
    return ip


def write_cache(cli_ip, host, ip, ttl):
    if ip:
        now = int(time.time())

        if not cache.get(cli_ip):
            cache[cli_ip] = dict()
        cache[cli_ip][host] = dict(
            ip=ip,
            ttl=ttl,
            querytime=now,
        )
    else:
        return


def query(req, host, client, pos):
    if pos == 'cn':
        by_socks = False
        by_httpdns = config['by_httpdns']
        dns_addr = dns_cn_addr
        cli_ip = client[0]
    else:
        by_socks = True
        by_httpdns = False
        dns_addr = dns_cn_addr
        cli_ip = 'default'
    resp, ip, ttl = get_dns(req, host, client[0],
                            dns_addr, by_socks, by_httpdns)
    server.sendto(resp, client)

    write_cache(cli_ip, host, ip, ttl)
    log(client, '[{}]'.format(pos), host, ip, '({})'.format(ttl))


def query_cn_website(req, host, client):
    query(req, host, client, 'cn')


def query_foreign_website(req, host, client):
    query(req, host, client, 'foreign')


def host_timeout(cli_ip, host):
    query_time = cache[cli_ip][host]['querytime']
    now = int(time.time())
    return now - query_time


def in_cache(cli_ip, host):
    if cli_ip in cache and host in cache[cli_ip]:
        ttl = cache[cli_ip][host]['ttl']
        return host_timeout(cli_ip, host) <= ttl
    else:
        return False


def handle_in_cache(cli_ip, host, req, cli_addr):
    ip, ttl = cache[cli_ip][host]['ip'], cache[cli_ip][host]['ttl']
    current_ttl = ttl - host_timeout(cli_ip, host)
    server.sendto(make_data(req, ip, current_ttl), cli_addr)
    log(cli_addr, '[cache]', host, ip, '({})'.format(current_ttl))


def handle_query(req, host, client):
    # ip = cache[name]
    if inlist(host, white_list):
        if in_cache(client[0], host):
            cli_ip = client[0]
            handle_in_cache(cli_ip, host, req, client)
        else:
            query_cn_website(req, host, client)

    else:
        mode = 'default'
        if in_cache(mode, host):
            handle_in_cache('default', host, req, client)
            # ip = cache['default'][host]['ip']
            # ttl = cache['default'][host]['ttl']
            # current_ttl = ttl - host_timeout('default', host)
            # server.sendto(make_data(req, ip, current_ttl), client)
            # log(client, '[cache]', host, ip, '({})'.format(current_ttl))
        else:
            query_foreign_website(req, host, client)


def handle(data, client):
    list_iter = iter(data[13:])
    name = ''
    for bit in iter(lambda: next(list_iter), 0):
        name += '.' if bit < 32 else chr(bit)

    type = unpack('>H', data[14+len(name):16+len(name)])
    type = type[0]

    # 非A类请求
    if not type:
        resp, ip = get_dns(name, data, client[0], dns_cn_addr, by_socks=False,
                           by_httpdns=config['by_httpdns'])
        server.sendto(resp, client)
        return

    # 广告
    elif inlist(name, ad):
        ip = '127.0.0.1'
        print(client[0],
              '[{}]'.format(time.strftime('%Y-%m-%d %H:%M:%S')),
              '[ad]', name, ip)
        server.sendto(make_data(data, ip, 3600), client)

    # 命中缓存
    else:
        handle_query(data, name, client)


def serv_start(handle):
    global socket, server, cache
    geventsocks.set_default_proxy(config['socks5_ip'], config['socks5_port'])
    server = DatagramServer((config['listen_ip'], config['listen_port']),
                            handle)
    cache = {}
    return server.serve_forever()


def bjdns():
    global white_list, ad, config
    global dns_cn_addr, dns_foreign_addr

    with open('whitelist.txt', 'r') as f:
        white_list = {x: True for x in f.read().split('\n') if x}

    with open('ad.txt', 'r') as f:
        ad = {x: True for x in f.read().split('\n') if x}\
            if os.path.isfile('ad.txt') else {}

    if len(sys.argv) >= 2:
        json_dir = sys.argv[1]
    else:
        json_dir = 'bjdns.json'
    json_str = open(json_dir).read()
    config = json.loads(json_str)
    # config = config
    log(config)
    # listen_addr = (config['listen_ip'], config['listen_port'])
    dns_cn_addr = (config['dns_cn_ip'],
                   config['dns_cn_port'])
    dns_foreign_addr = (config['dns_foreign_ip'],
                        config['dns_foreign_port'])

    serv_start(handle)


if __name__ == '__main__':
    bjdns()
