import time
from utils import log

class Cache:
    def __init__(self):
        self.cache = dict()

    def write(self, src_ip: str, resp: map):
        if resp.get('Status') != 0:
            return

        questions = resp.get('Question')

        if not self.cache.get(src_ip):
            self.cache[src_ip] = dict()

        for question in questions:
            key = (question.get('type'), question.get('name'))
            self.cache[src_ip][key] = dict()
            self.cache[src_ip][key]['mtime'] = int(time.time())
            self.cache[src_ip][key]['response'] = resp

    def select(self, src_ip: str, question: map):
        dns_type, name = question.get('type'), question.get('name')
        if not name.endswith('.'):
            name += '.'

        value = self.cache.get(src_ip, {}).get((dns_type, name))
        # log((dns_type, name), value, self.cache.get(src_ip, {}))

        if value:
            now = time.time()
            for answer in value['response']['Answer']:
                # log(answer, now - value['mtime'], answer['TTL'])
                if now - value['mtime'] > answer['TTL']:
                    log(question['name'], 'Need update')
                    return None
            else:
                return value['response']

        else:
            return None
