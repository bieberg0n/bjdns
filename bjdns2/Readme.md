# bjdns2

bjdns2的开发初衷是希望未来的DNS请求都能经过加密，保证隐私。  
bjdns2分为服务端和客户端：  
* 服务端启动一个HTTP服务器，提供HTTPDNS查询服务（强烈建议加上TLS证书）；
* 客户端在本地运行，通过HTTP(S)与服务端连接并发起请求。  

### Usage  
#### Server:
1. Install Python3, gevent, flask:
```
$ sudo apt install python3 python3-pip
$ sudo pip3 install gevent flask
```
2. Clone:
```
$ git clone https://github.com/bieberg0n/bjdns.git
$ cd bjdns
$ git checkout dev
$ cd bjdns2
```

3. Edit config, if you have TLS cert.  
If your server is in China, you need run Shadowsocks and the listen port is 1080; Or not, take proxy to 'False'.
```
$ cp bjdns2_config_example.py bjdns2_config.py
$ nano bjdns2_config.py
```

4. Run:
```
$ ./start.sh
```

5. Test:
```
curl https://your.domain.name/?dn=twitter.com
```

#### Client:
1. Do server usage 1 - 3;

2. Edit config, add bjdns2 server domain name and IP;

3. Run:
```
$ sudo python3 bjdns2_client.py
```

4. Test:
```
dig www.twitter.com @127.0.0.1
```

### License (GNU GPL3)  
Copyright (c) 2017 bjong
