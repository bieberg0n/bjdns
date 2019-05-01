# BJDNS3

BJDNS3 is a simple DNS server which can protect yourself against DNS poisoning for Chinese general user.   

## Usage  

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
$ ./bjdns3 -h
Usage:
  bjdns3 [--debug] [-d <DIRECT_DNS_SERVER>] [-l <LISTEN_IP_PORT>]

Examples:
  bjdns3 -d "119.29.29.29"

Options:
  -h --help             Show this screen
  -d DIRECT_DNS_SERVER  dns server for Chinese host. default: 223.5.5.5
  -l LISTEN_IP_PORT     listen ip and port. default: 0.0.0.0:53
  --debug               debug mode
```

Run:
```
$ sudo ./bjdns3
```

5. Test:
```
dig www.twitter.com @127.0.0.1
```

6. Now you can set your system's dns to "127.0.0.1".  

## Thanks
The **whitelist.json** file is modified from the file in [breakwa11](https://github.com/breakwa11)'s [gfw_whitelist](https://github.com/breakwa11/gfw_whitelist) project. The project uses the [MIT](https://github.com/breakwa11/gfw_whitelist/blob/master/LICENSE) license.  

## License (GNU GPL3.0)  
Copyright (c) 2017-2019 bjong
