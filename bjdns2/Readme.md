# bjdns2

The original intention of bjdns2 development is to hope that future DNS requests can be encrypted to ensure privacy.  

bjdns2 is divided into server and client：  
* The server starts an HTTP server, providing HTTPDNS query service (TLS certificate is strongly recommended);  
* The client runs locally, connects to the server over HTTP (S) and initiates the request.  

### Usage  
I have set up a bjdns2 server on g.bjong.me:5353. So you can just run bjdns2 client to try it.  

#### Client:
1. Install Python3:
```
$ sudo apt install python3 python3-pip
```

2. Clone:
```
$ git clone https://github.com/bieberg0n/bjdns.git
$ cd bjdns/bjdns2
```

3. Install requires:
```
$ sudo pip3 install -r requirements.txt
```

4. Client usage:
```
$ python3 bjdns2_client.py -h
Usage:
  bjdns2_client.py (-s <BJDNS2_SERVER_ADDR>) (-i <BJDNS2_SERVER_IP>)
  bjdns2_client.py (-c <CONFIG_FILE>)


Examples:
  bjdns2_client.py -s "https://your.domain.name:your_port" -i "127.0.0.1"
  bjdns2_client.py -c "config.json"

Options:
  -h --help             Show this screen
  -s BJDNS2_SERVER_ADDR bjdns2 server address
  -i BJDNS2_SERVER_IP   bjdns2 server ip
  -c CONFIG_FILE        path to config file
```
You can use my bjdns2 server directly:
```
$ sudo python3 bjdns2_client.py -s "https://g.bjong.me:5353" -i "116.196.98.219"
```

Or use config file:
```
$ cp config_example.json config.json  
$ nano config.json  # Edit bjdns2 server addr and ip
$ sudo python3 bjdns2_client.py -c config.json  # run
```
5. Test:
```
dig www.twitter.com @127.0.0.1
```

6. Now you can set your system's dns to "127.0.0.1".  

#### Server:
1. Do client usage 1 - 3;

2. Edit config, if you have TLS cert.  
If your server is in China, you need run Shadowsocks and the listen port is 1080; Or not, take proxy to 'False'.
```
$ cp config_example.json config.json  
$ nano config.json
```

4. Run:
```
$ sudo python3 bjdns2.py
```

5. Test:
```
curl https://your.domain.name/?dn=twitter.com
```


### Thinks
The **whitelist.json** file is modified from the file in [breakwa11](https://github.com/breakwa11)'s [gfw_whitelist](https://github.com/breakwa11/gfw_whitelist) project. The project uses the [MIT](https://github.com/breakwa11/gfw_whitelist/blob/master/LICENSE) license.  

### License (GNU GPL3.0)  
Copyright (c) 2017 bjong
