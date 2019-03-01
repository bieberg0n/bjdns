# -*- coding: utf-8 -*-

import IPy
import re


def read_ip_dat(file):
    with open(file) as f:
        net_range_list = [net_range.rstrip() for net_range in f.readlines()]
    p = re.compile('/.+$')
    del_z = lambda net: p.sub('', net)
    net_int_list = [ip_to_int(del_z(net)) for net in net_range_list]
    return net_range_list, net_int_list


def ip_to_int(ip):
    ip = ip.split('.')
    add_zero = lambda n: '0' * (3-len(n)) + n
    ip_str = ''.join([add_zero(n) for n in ip])
    return int(ip_str)


def get_best_net_int(ip, net_int_list):
    sn = len(net_int_list) // 2
    # print(ip, sn, net_int_list[sn], len(net_int_list))
    if len(net_int_list) == 2 and ip >= net_int_list[sn]:
        return net_int_list[sn]
    elif net_int_list[sn] <= ip < net_int_list[sn+1]:
        return net_int_list[sn]
    elif ip > net_int_list[sn]:
        return get_best_net_int(ip, net_int_list[sn:])
    else:  # ip < net_int_list:
        return get_best_net_int(ip, net_int_list[:sn+1])


def get_best_net(ip, net_range_list, net_int_list):
    ip = ip_to_int(ip)
    best_net_int = get_best_net_int(ip, net_int_list)
    best_sn = net_int_list.index(best_net_int)
    return net_range_list[best_sn]


def ip_in_cn_gen():
    dat_file = 'cn_ip.txt'
    # IP = IPy.IP
    net_range_list, net_int_list = read_ip_dat(dat_file)

    def f(ip):
        best_net_range = get_best_net(ip, net_range_list, net_int_list)
        return ip in IPy.IP(best_net_range)
    return f


if __name__ == "__main__":
    ip_in_cn = ip_in_cn_gen()
    print(ip_in_cn('124.225.171.2'))
    print(ip_in_cn('49.114.165.195'))
    # for ip in ['49.114.165.195',
    #            '211.137.180.236',
    #            '175.223.16.46',
    #            '175.223.52.32',
    #            '219.74.86.136',
    #            '223.62.178.66',
    #            '223.33.184.117',
    #            '222.102.171.135',
    #            '113.162.202.32',
    #            '37.131.68.47',
    #            '178.77.154.240',
    #            '186.204.91.244',
    #            '119.139.14.70',
    #            '103.1.30.66',
    #            '192.168.102.42',
    #            '171.208.114.19',
    #            '27.42.26.56',
    #            '49.114.165.195',
    #            '211.137.180.236',
    #            '175.223.16.46',
    #            '175.223.52.32',
    #            '219.74.86.136',
    #            '223.62.178.66',
    #            '223.33.184.117',
    #            '222.102.171.135',
    #            '113.162.202.32',
    #            '37.131.68.47',
    #            '178.77.154.240',
    #            '186.123.135.229',
    #            '61.18.254.113',
    #            '210.91.142.47',
    #            '223.255.252.1']:
    # print(ip, ip_in_china(ip, net_range_list))
