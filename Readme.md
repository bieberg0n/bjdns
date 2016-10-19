#bjdns

一个简单的带缓存的DNS服务器，用于防止DNS污染。  
在阿里云的一个服务器上已部署了本项目，自家宽带若是电信的话可以把dns设为121.42.185.92即可，若使用遇到问题再改为本地部署。

###Feature
* 2016-10-19  
从本次更新开始bjdns需要配合shadowsocks或其他socks5代理使用。  
在bjdns.json中填写shadowsocks客户端监听的ip地址（不要填域名）与端口，默认为 127.0.0.1:1080 。

* 2016-04-29  
加入过滤广告功能,如果不需要这个功能可自行删除ad.txt .  

###Support
Windows/Linux/OS X

###Depends
Python(>=3)  
requests  
gevent  
python-tkinter  
[Winico](https://github.com/lijiejie/python-flash-trayicons/tree/master/winico0.6)(仅Windows依赖)  
p.s. 打包版已内置以上依赖。

###Usage
####Linux/OS X:
1 安装Python3.  
2 安装依赖:
> $ sudo pip3 install --upgrade requests gevent

3 确保本地（或别的地方）的shadowsocks客户端已开启，确认bjdns.json中填写正确  
4 修改本机DNS为127.0.0.1，然后在终端输入  
>$ sudo python3 bjdns.py  

####Windows:
1 下载打包版[点我](https://github.com/bieberg0n/bjdns/releases)  
2 确保本地（或别的地方）的shadowsocks客户端已开启，确认bjdns.json中填写正确  
3 在网络连接的本地连接(或者无线网络)-属性-IPv4里，将首选DNS服务器改为127.0.0.1  
4 启动目录中的bjdns.exe。  
5 任务栏图标右键弹出菜单可退出。  

###Reference
[Python 实现DNS服务器(Pyhon域名解析服务器)](http://blog.csdn.net/trbbadboy/article/details/8093256)  
[Python使用winIco编写一个托盘图标不停闪烁的小程序](http://www.lijiejie.com/python-winico-flash-trayicon/)

###Authors
bjong

###License (MIT)
Copyright (c) 2015-2016 bjong
