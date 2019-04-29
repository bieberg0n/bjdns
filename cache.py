import time
from utils import info


def host_add_dot(host):
    if not host.endswith('.'):
        host += '.'
    return host


class Cache:
    def __init__(self):
        self.cache = dict()

    def write(self, src_ip: str, question: map, resp) -> None:
        if not self.cache.get(src_ip):
            self.cache[src_ip] = dict()

        q_type, name = question.get('type'), host_add_dot(question.get('name'))
        key = (q_type, name)
        self.cache[src_ip][key] = dict()
        self.cache[src_ip][key]['mtime'] = int(time.time())

        self.cache[src_ip][key]['data'] = resp.raw
        self.cache[src_ip][key]['ttl'] = resp.ttl

    def select(self, src_ip: str, question: map):
        dns_type, name = question.get('type'), question.get('name')
        name = host_add_dot(name)

        try:
            value = self.cache.get(src_ip).get((dns_type, name))
            response = value.get('response')
        except Exception:
            return None
        else:
            # log((dns_type, name), value, self.cache.get(src_ip, {}))
            now = time.time()
            if response:
                ttls = [answer['TTL'] for answer in value['response']['Answer']]
                resp = value['response']
            else:
                resp = value['data']
                ttls = [value['ttl']]
                # log(answer, now - value['mtime'], answer['TTL'])

            for ttl in ttls:
                if now - value['mtime'] > ttl:
                    info(question['name'], 'Need update')
                    return None
            else:
                return resp
