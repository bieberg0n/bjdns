#!/usr/bin/env python3
# coding=utf-8

# copyright 2016 bjong

import sys
import os
import time
import json
import re
import struct
from struct import pack, unpack
from gevent.server import DatagramServer
from gevent import socket, monkey
import geventsocks
monkey.patch_all()
import requests


s = requests.session()


def inlist(name, dict_):
    name = name.split('.')
    name.reverse()
    for i in range(1,len(name)+1):
        name_ = list(reversed([ name[j] for j in range(i) ]))
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
        ag = (mark<<16) & numIp
        if ip3 ==ag:
            return True
        ag = mark<<20 & numIp
        if ip2 == ag:
            return True
        ag = (mark<<24) & numIp
        if ip1 == ag:
            return True
        return False


def get_dns_by_http(domain_name, client_ip):
    if is_private_ip(client_ip):
        r = s.get('http://119.29.29.29/d?dn={}&ip={}'.format(domain_name, ''))
    else:
        r = s.get('http://119.29.29.29/d?dn={}&ip={}'.format(domain_name, client_ip))
    # print(r.text)
    ip = r.text.split(';')[0]
    if ip:
        return (ip)
    else:
        return ''


def get_dns_by_tcp(query_data, dns_server, by_socks=False):
    data = pack('>H', len(query_data)) + query_data

    if by_socks:
        # if config['mode'] == 'gevent':
        s = socket.socket()
        geventsocks.connect(s, dns_server)
        # else:
        #     s = socks.socksocket()
        #     s.connect(dns_server)
    else:
        s = socket.socket()
        s.connect(dns_server)

    s.send(data)
    # res = b''
    # while len(res) <= 2:
    res = s.recv(512)
    if len(res) <= 2:
        s.close()
        # return make_data(query_data, '127.0.0.1')
        return b''
    else:
        # length = unpack('>H', res[:2])[0]
        # if length <= len(res) - 2:
        #     pass
        # else:
        #     while len(res) - 2 < length:
                # res += s.recv(512)
        s.close()
        return res[2:]


def get_dns(domain_name, query_data, client_ip, dns_server, by_socks=False, by_httpdns=False):
    if by_socks or not by_httpdns:
        resp = get_dns_by_tcp(query_data, dns_server, by_socks)
        ip = get_ip_from_resp(resp, len(query_data))
        return (resp, ip)
    else:
        ip = get_dns_by_http(domain_name, client_ip)
        if ip:
            resp = make_data(query_data, ip)
        else:
            resp = b''

    return (resp, ip)
    # else:
# def get_data(data, dns_addr=()):
#     '''get data by udp'''
#     s = socket.socket()
#     if timeout:
#         s.settimeout(0.5)
#     else:
#         pass
#     if dns_addr:
#         s.connect(dns_addr)
#     else:
#         s.connect(dns_cn_addr)
#     # s.connect(dns_addr)
#     data = pack('>H', len(data)) + data
#     s.send(data)
#     resp = s.recv(512)
#     return resp[2:]


# def get_foreign_data(data):
#     '''get data by another dns server'''
#     # try:
#     #     resp = get_data(data, ('123.207.137.88', 53), timeout=True)
#     #     return resp
#     # except socket.timeout:
#     data = pack('>H', len(data)) + data
#     if config['mode'] == 'gevent':
#         s = socket.socket()
#         geventsocks.connect(s, dns_foreign_addr)
#     else:
#         s = socks.socksocket()
#         s.connect(dns_foreign_addr)
#     s.send(data)
#     res = s.recv(512)
#     length = unpack('>H', res[:2])[0]
#     if length <= len(res) - 2:
#         pass
#     else:
#         while len(res) - 2 < length:
#             res += s.recv(512)
#     s.close()
#     return res[2:]


def make_data(data, ip):
    #data is request
    (id, flags, quests,
     answers, author, addition) = unpack('>HHHHHH', data[0:12])
    flags_new   = 33152
    answers_new = 1
    res         = pack('>HHHHHH', id, flags_new, quests,
                       answers_new, author, addition)

    res        += data[12:]

    dns_answer  = {
        'name':49164,
        'type':1,
        'classify':1,
        'ttl':600,
        'datalength':4
        }
    res        += pack('>HHHLH', dns_answer['name'], dns_answer['type'],
                      dns_answer['classify'], dns_answer['ttl'],
                      dns_answer['datalength'])

    ip          = ip.split('.')
    # print(ip)
    try:
        ip_bytes    = pack('BBBB', int(ip[0]), int(ip[1]),
                           int(ip[2]), int(ip[3]))
    except ValueError as e:
        print(cache)

    res        += ip_bytes
    return res


def get_ip_from_resp(res, data_len):
    ip=''
    p = re.compile(b'\xc0.\x00\x01\x00\x01')
    # print(res)
    try:
        res = p.split(res)[1]
        ip_bytes   = unpack('BBBB',res[6:10])
        ip         =  '.'.join( [ str(i) for i in ip_bytes ] )
    except IndexError as e:
        # print(e, res)
        pass
    return ip


def eva(data, client):
    list_iter = iter(data[13:])
    name      = ''
    for bit in iter(lambda: next(list_iter), 0):
        name += '.' if bit < 32 else chr(bit)

    type = unpack('>H',data[14+len(name):16+len(name)])
    type = type[0]

    # 非A类请求
    if not type:
        resp, ip = get_dns(name, data, client[0], dns_cn_addr, by_socks=False, by_httpdns=config['by_httpdns'])
        server.sendto(resp, client)
        return

    # 命中缓存
    elif name in cache:
        ip = cache[name]
        print(client[0],
              '[{}]'.format(time.strftime('%Y-%m-%d %H:%M:%S')),
              '[cache]', name, ip)
        server.sendto(make_data(data, ip), client)
        resp, ip_new = get_dns(name, data, client[0], dns_foreign_addr, by_socks=True)
        if ip_new and ip_new != ip:
            cache[name] = ip_new

    # 广告
    elif inlist(name, ad):
        ip = '127.0.0.1'
        print( client[0],
               '[{}]'.format(time.strftime('%Y-%m-%d %H:%M:%S')),
               '[ad]', name, ip)
        server.sendto(make_data(data, ip), client)

    # 国内网站
    elif inlist(name, white_list):
        resp, ip = get_dns(name, data, client[0], dns_cn_addr, by_socks=False, by_httpdns=config['by_httpdns'])
        print(client[0],
              '[{}]'.format(time.strftime('%Y-%m-%d %H:%M:%S')),
              '[cdn]', name, ip)
        # res = get_dns_by_tcp(data, dns_cn_addr)
        server.sendto(resp, client)
        # ip = get_ip_from_resp(res, len(data))
        # cache[name] = ip

    # 国外网站
    else:
        resp, ip = get_dns(name, data, client[0], dns_foreign_addr, by_socks=True)
        server.sendto(resp, client)
        print(client[0],
              '[{}]'.format(time.strftime('%Y-%m-%d %H:%M:%S')),
              name, ip)
        if ip:
            cache[name] = ip
            print(cache, ip)
        else:
            pass


def serv_start(handle):
    global socket, server, cache
    # mode = config['mode']
    # if mode == 'gevent':
    # global geventsocks
    geventsocks.set_default_proxy(config['socks5_ip'], config['socks5_port'])
    server = DatagramServer((config['listen_ip'], config['listen_port']), handle)
    cache = {}
    return server.serve_forever()

    # elif mode == 'multiprocessing':
    #     global socks
    #     import socket
    #     import multiprocessing
    #     import socks
    #     socks.set_default_proxy(socks.SOCKS5, config['socks5_ip'], config['socks5_port'])
    #     server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #     server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #     server.bind((config['listen_ip'], config['listen_port']))
    #     cache = multiprocessing.Manager().dict()
    #     pool = multiprocessing.Pool(config['the_num_of_processes'])
    #     while True:
    #         data, cli_addr = server.recvfrom(512)
    #         pool.apply_async(handle, args=(data, cli_addr,))


def main():
    global white_list, ad, config
    global dns_cn_addr, dns_foreign_addr

    white_list = { x:True for x in open('whitelist.txt','r').read().split('\n') if x}

    ad = { x:True for x in open('ad.txt','r').read().split('\n') if x} if os.path.isfile('ad.txt') else {}

    if len(sys.argv) >= 2:
        json_dir = sys.argv[1]
    else:
        json_dir = 'bjdns.json'
    json_str = open(json_dir).read()
    json_dict = json.loads(json_str)
    config = json_dict
    listen_addr = (json_dict['listen_ip'], json_dict['listen_port'])
    dns_cn_addr = (json_dict['dns_cn_ip'], json_dict['dns_cn_port'])
    dns_foreign_addr = (json_dict['dns_foreign_ip'], json_dict['dns_foreign_port'])

    serv_start(eva)
    # exit()
    # if os.name != 'nt':
    #     serv_start(eva)
    #     # adem()
    #     # exit()

    # else:
    #     import threading
    #     import socket
    #     from tkinter import Tk, Menu#,messagebox

    #     def adem_thread(s):
    #         while 1:
    #             try:
    #                 data, client = s.recvfrom(512)
    #                 threading.Thread(target=eva,args=(data, client,)).start()
    #             except ConnectionResetError:
    #                 pass

    #     def menu_func(event, x, y):
    #         if event == 'WM_RBUTTONDOWN':    # Right click tray icon, pop up menu
    #             menu.tk_popup(x, y)


    #     def quit():
    #         root.quit()
    #         root.destroy()
    #         sys.exit()

    #     s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #     s.bind( listen_addr )

    #     root = Tk()
    #     root.tk.call('package', 'require', 'Winico')
    #     icon = root.tk.call('winico', 'createfrom', os.path.join(os.getcwd(), 'py.ico'))    # New icon resources
    #     root.tk.call('winico', 'taskbar', 'add', icon,
    #                  '-callback', (root.register(menu_func), '%m', '%x', '%y'),
    #                  '-pos',0,
    #                  '-text','bjdns')
    #     menu = Menu(root, tearoff=0)
    #     menu.add_command(label='退出', command=quit)

    #     root.withdraw()
    #     t = threading.Thread(target=adem_thread, args=(s,))
    #     t.setDaemon(True)
    #     t.start()
    #     root.mainloop()


if __name__ == '__main__':
    main()
