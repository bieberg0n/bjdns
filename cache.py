import time
from utils import log


def host_add_dot(host):
    if not host.endswith('.'):
        host += '.'
    return host


class Cache:
    def __init__(self):
        self.cache = dict()

    def write(self, src_ip: str, question: map, resp: map, data: bytes) -> None:
        if resp and resp.get('Status') != 0:
            return

        # questions = resp.get('Question')

        if not self.cache.get(src_ip):
            self.cache[src_ip] = dict()

        # for question in questions:
        q_type, name = question.get('type'), host_add_dot(question.get('name'))
        key = (q_type, name)
        self.cache[src_ip][key] = dict()
        self.cache[src_ip][key]['mtime'] = int(time.time())
        if resp:
            self.cache[src_ip][key]['response'] = resp
        else:
            self.cache[src_ip][key]['data'] = data

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
                ttls = [300]
                resp = value['data']
                # log(answer, now - value['mtime'], answer['TTL'])

            for ttl in ttls:
                if now - value['mtime'] > ttl:
                    log(question['name'], 'Need update')
                    return None
            else:
                return resp
