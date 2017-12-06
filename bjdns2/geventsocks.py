
# copyright 2016 bjong

from struct import pack
from gevent import socket

_proxy_dst = None
_proxy_port = None
def set_default_proxy(proxy_serv, port):
    global _proxy_dst, _proxy_port
    _proxy_dst = proxy_serv
    _proxy_port = port


def valid_ip(address):
    try:
        ip_bytes = socket.inet_aton(address)
        return ip_bytes
    except:
        return False

def connect(sock, addr):
    sock.connect( (_proxy_dst, _proxy_port) )
    sock.sendall(b'\x05\x01\x00')
    r = sock.recv(512)
    if r == b'\x05\x00':
        pass
    else:
        raise Exception("connect fail")

    dst, port = addr
    ip_bytes = valid_ip(dst)
    if ip_bytes:
        # ip = dst.split('.')
        # ip_bytes = pack('BBBB', int(ip[0]), int(ip[1]),
        #                 int(ip[2]), int(ip[3]))
        # ip_bytes = socket.inet_aton(dst)
        port_bytes = pack('>H', port)
        sock.sendall(b'\x05\x01\x00\x01' + ip_bytes + port_bytes)
    else:
        dst_bytes = dst.encode()
        len_dst_bytes = pack('B', len(dst_bytes))
        port_bytes = pack('>H', port)
        sock.sendall(b'\x05\x01\x00\x03' + len_dst_bytes + dst_bytes
                      + port_bytes)

    r = sock.recv(512)
    if r.startswith(b'\x05\x00'):
        pass
    else:
        raise Exception("connect fail")


if __name__ == '__main__':
    # print(valid_ip('8.8.8.8'))
    # exit()
    set_default_proxy('127.0.0.1', 1080)
    from gevent import socket
    s = socket.socket()
    connect(s, ('8.8.8.8', 53))
