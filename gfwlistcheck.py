import base64
import urllib.parse
from utils import (
    dict_deep_set
)


class GfwList:
    def __init__(self):
        self.data = dict()
        self.read_line()

    def add_host(self, host):
        parts = [part for part in reversed(host.split('.')) if part]
        dict_deep_set(self.data, parts)

    def read_line(self):
        with open('gfwlist.txt') as f:
            txt = f.read()

        txt = base64.b64decode(txt).decode()
        lines = txt.split('\n')

        for line in lines:
            if line == '' or line[0] in ('[', '!', '@'):
                continue

            elif line.startswith('|http'):
                url = urllib.parse.urlsplit(line[1:])
                host = url.netloc
                self.add_host(host)

            elif line.startswith('||'):
                self.add_host(line[2:])

            elif '/' not in line:
                self.add_host(line)

    def check(self, host):
        d = self.data
        parts = [part for part in reversed(host.split('.')) if part]
        for part in parts[:-1]:
            if d.get(part):
                d = d[part]
            else:
                return False

        else:
            return d.get(parts[-1]) is not None


if __name__ == '__main__':
    gfwlist = GfwList()
