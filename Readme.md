#bjdns

一个简单的带缓存的 DNS 服务器，用于防止 DNS 污染。  

---

在阿里云的一个服务器上已部署了本项目，自家宽带若是电信的话可以把 dns 设为121.42.185.92 即可，若使用遇到问题再改为本地部署。

####其他有类似效果的 DNS 服务器
* 中国科技大学
	* 202.141.176.93
	* 202.141.162.123
	* 202.38.93.153

* [UDNS](http://tieba.baidu.com/p/4432093605)
	* 115.159.157.26
	* 115.159.158.38 (可上 Google / wiki / Twitter )

---

###Feature
* 2016-10-19  
从本次更新开始 bjdns 需要配合 shadowsocks 或其他 socks5 代理使用。  
在 bjdns.json 中填写 shadowsocks 客户端监听的 ip 地址（不要填域名）与端口，默认为 127.0.0.1:1080 。

* 2016-04-29  
加入过滤广告功能,如果不需要这个功能可自行删除 ad.txt .  

###Support
Windows/Linux/OS X

###Depends
Python(>=3)  
gevent  
python-tkinter  
[Winico](https://github.com/lijiejie/python-flash-trayicons/tree/master/winico0.6)(仅 Windows 依赖)  
p.s. 打包版已内置以上依赖。

###Usage
####Linux/OS X:
1 安装Python3.  
2 安装bjdns:
```
git clone https://github.com/bieberg0n/bjdns.git  
cd bjdns  
sudo python3 setup.py install

```

3 确保本地（或别的地方）的 shadowsocks 客户端已开启，确认 bjdns/bjdns.json 中填写正确  
4 修改本机 DNS 为 127.0.0.1 ，然后在终端输入  
```
sudo bjdns ./bjdns/bjdns.json  

```

####Windows:
1 下载打包版[点我](https://github.com/bieberg0n/bjdns/releases)  
2 确保本地（或别的地方）的 shadowsocks 客户端已开启，确认 bjdns.json 中填写正确  
3 在网络连接的本地连接(或者无线网络)-属性-IPv4里，将首选 DNS 服务器改为 127.0.0.1  
4 启动目录中的 bjdns.exe。  
5 任务栏图标右键弹出菜单可退出。  

###Reference
[Python 实现DNS服务器(Pyhon域名解析服务器)](http://blog.csdn.net/trbbadboy/article/details/8093256)  
[Python使用winIco编写一个托盘图标不停闪烁的小程序](http://www.lijiejie.com/python-winico-flash-trayicon/)

###Authors
bjong

###License (MIT)
Copyright (c) 2015-2016 bjong
