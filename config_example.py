import multiprocessing


bind = '0.0.0.0:5353'
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'gevent'
keepalive = 120

# 如需架设成HTTPS，取消这三注释并填好cert和key位置
# keyfile = ''
# certfile = ''
# ssl_version = 5

# 访问国外dns的时候是否走代理
# 代理续运行在本机1080端口，socks协议
# 如果服务端运行在国外云主机就不需要走代理了，填成False
by_proxy = True

accesslog = '-'
debug = False

# 白名单，使用国内DNS解析
# 如果bjdns服务端和shadowsocks同时运行在一台机器上的话，把ss服务器域名写这里
white_list = [
    '.bilibili.com',
]
