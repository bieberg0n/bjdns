# bjdns2

The original intention of bjdns2 development is to hope that future DNS requests can be encrypted to ensure privacy.  

bjdns2 is divided into server and client：  
* The server starts an HTTP server, providing HTTPDNS query service (TLS certificate is strongly recommended);  
* The client runs locally, connects to the server over HTTP (S) and initiates the request.  

## Usage  
I have set up a bjdns2 server on go.bjong.me:5353. So you can just run bjdns2 client to try it.  

### Client:
1. Install Python3:
```
$ sudo apt install python3 python3-pip
```

2. Clone:
```
$ git clone https://github.com/bieberg0n/bjdns.git
$ cd bjdns/
```

3. Install requires:
```
$ sudo pip3 install -r requirements.txt
```

4. Client usage:
```
$ python3 bjdns2_client.py -h
Usage:
  bjdns2_client.py (-s <BJDNS2_SERVER_ADDR>) (-i <BJDNS2_SERVER_IP>) [-d <DIRECT_DNS_SERVER>] [-b <LISTEN_IP_PORT>]

Examples:
  bjdns2_client.py -s "https://your.domain.name:your_port" -i "127.0.0.1" -d "119.29.29.29"

Options:
  -h --help             Show this screen
  -s BJDNS2_SERVER_ADDR bjdns2 server address
  -i BJDNS2_SERVER_IP   bjdns2 server ip
  -d DIRECT_DNS_SERVER  dns server, be used when query type is not A
  -b LISTEN_IP_PORT     listen ip and port
```
You can use my bjdns2 server directly:
```
$ sudo python3 bjdns2_client.py -s "https://go.bjong.me:5353" -i "116.196.98.219"
```

5. Test:
```
dig www.twitter.com @127.0.0.1
```

6. Now you can set your system's dns to "127.0.0.1".  

### Server:
1. Do client usage 1 - 3;

2. Edit config, if you have TLS cert;  
And if your server is in China, you need run Shadowsocks and the listen port is 1080; Or not, take "by_proxy" to "False".
```
$ cp config_example.py config.py  
$ nano config.py
```

4. Run:
```
$ gunicorn -c config.py bjdns2:app
```

5. Test:
```
curl https://your.domain.name/?dn=twitter.com
```


## Thanks
The **whitelist.json** file is modified from the file in [breakwa11](https://github.com/breakwa11)'s [gfw_whitelist](https://github.com/breakwa11/gfw_whitelist) project. The project uses the [MIT](https://github.com/breakwa11/gfw_whitelist/blob/master/LICENSE) license.  

## License (GNU GPL3.0)  
Copyright (c) 2017-2018 bjong
