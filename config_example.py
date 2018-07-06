import multiprocessing


bind = '0.0.0.0:5353'
workers = multiprocessing.cpu_count() * 2 + 1
keepalive = 120
worker_class = 'gevent'
# keyfile = ''
# certfile = ''
# ssl_version = 5
by_proxy = True