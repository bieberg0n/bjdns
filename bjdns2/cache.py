import time


class Cache():
    def __init__(self):
        self.cache = {}

    def write(self, host, cli_ip, ip, ttl):
        now = int(time.time())

        if not self.cache.get(host):
            self.cache[host] = dict()

        self.cache[host][cli_ip] = dict(
            ip=ip,
            ttl=ttl,
            querytime=now,
        )

    def host_timeout(self, host, cli_ip):
        query_time = self.cache[host][cli_ip]['querytime']
        now = int(time.time())
        return now - query_time

    def select(self, host, cli_ip):
        if self.cache.get(host) and self.cache.get(host).get(cli_ip):
            data = self.cache[host][cli_ip]
            ip = data['ip']
            ttl = data['ttl']
            # timeout = self.host_timeout(host, cli_ip)
            # if timeout > ttl:
            #     return data['ip'], ttl
            # else:
            #     current_ttl = ttl - timeout
            #     return data['ip'], current_ttl
            return ip, ttl
        else:
            return '', 0
