# bjdns

一个简单的带缓存的 DNS 服务器，用于防止 DNS 污染。  

---

#### 其他有类似效果的 DNS 服务器
* 中国科技大学
	* 202.141.176.93
	* 202.141.162.123
	* 202.38.93.153

* [PureDNS](http://puredns.cn)
	* 123.207.137.88 (可上 Google / wiki / Twitter )

---

### Feature
* 2016-12-24  
可以将并发模式切换成异步或多进程，在 bjdns.json 中设置
```
"mode":"gevent" or "multiprocessing"
"the_num_of_processes":16		# only work by multiprocessing
```


* 2016-10-19  
从本次更新开始 bjdns 需要配合 shadowsocks 或其他 socks5 代理使用。  
在 shadowsocks 客户端的 server 设置中应填写 IP，不能为域名。  
在 bjdns.json 中填写 shadowsocks 客户端监听的 ip 地址（也不要填域名）与端口，默认为 127.0.0.1:1080 。

* 2016-04-29  
加入过滤广告功能,如果不需要这个功能可自行删除 ad.txt .  

### Support
Windows/Linux/OS X

### Depends
Python(>=3)  
gevent  
python-tkinter  
[Winico](https://github.com/lijiejie/python-flash-trayicons/tree/master/winico0.6)(仅 Windows 依赖)  
p.s. 打包版已内置以上依赖。

### Usage  
#### Linux/OS X:  
1 Install Python3 and pip;  
2 Install gevent:
```
sudo pip3 install gevent
```

2 clone bjdns:
```
git clone https://github.com/bieberg0n/bjdns.git  
cd bjdns  

```

3 确保本地（或别的地方）的 shadowsocks 客户端已开启，确认 bjdns/bjdns.json 中填写正确  
4 修改本机 DNS 为 127.0.0.1 ，然后在终端输入  
```
sudo python3 bjdns.py bjdns.json  

```

#### Windows:  
1 下载打包版[点我](https://github.com/bieberg0n/bjdns/releases)  
2 确保本地（或别的地方）的 shadowsocks 客户端已开启，确认 bjdns.json 中填写正确  
3 在网络连接的本地连接(或者无线网络)-属性-IPv4里，将首选 DNS 服务器改为 127.0.0.1  
4 启动目录中的 bjdns.exe。  
5 任务栏图标右键弹出菜单可退出。  

### Reference  
[Python 实现DNS服务器(Pyhon域名解析服务器)](http://blog.csdn.net/trbbadboy/article/details/8093256)  
[Python使用winIco编写一个托盘图标不停闪烁的小程序](http://www.lijiejie.com/python-winico-flash-trayicon/)

### Authors  
bjong

### License (MIT)  
Copyright (c) 2015-2016 bjong
