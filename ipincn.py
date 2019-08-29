# -*- coding: utf-8 -*-

import IPy


class CnIpChecker:
    def __init__(self):
        self.dat_file = 'cn_ip.txt'
        self.pool = dict()
        self.read_file()

    def read_file(self):
        with open(self.dat_file) as f:
            txt = f.read()

        for line in txt.split('\n'):
            parts = line.split('/', 2)
            ip = parts[0]
            mask = int(parts[1])
            if not self.pool.get(mask):
                self.pool[mask] = set()
            self.pool[mask].add(ip)

    def check(self, ip):
        for mask in range(32, 9, -1):
            ip_range = str(IPy.IP(ip).make_net(mask).net())
            if ip_range in self.pool[mask]:
                return True
        else:
            return False


if __name__ == "__main__":
    # ip_in_cn = ip_in_cn_gen()
    checker = CnIpChecker()
    print(checker.check('124.225.171.2'))
    print(checker.check('49.114.165.195'))
    for ip in ['49.114.165.195',
               '211.137.180.236',
               '175.223.16.46',
               '175.223.52.32',
               '219.74.86.136',
               '223.62.178.66',
               '223.33.184.117',
               '222.102.171.135',
               '113.162.202.32',
               '37.131.68.47',
               '178.77.154.240',
               '186.204.91.244',
               '119.139.14.70',
               '103.1.30.66',
               '192.168.102.42',
               '171.208.114.19',
               '27.42.26.56',
               '49.114.165.195',
               '211.137.180.236',
               '175.223.16.46',
               '175.223.52.32',
               '219.74.86.136',
               '223.62.178.66',
               '223.33.184.117',
               '222.102.171.135',
               '113.162.202.32',
               '37.131.68.47',
               '178.77.154.240',
               '186.123.135.229',
               '61.18.254.113',
               '210.91.142.47',
               '223.255.252.1']:
        print(ip, checker.check(ip))
