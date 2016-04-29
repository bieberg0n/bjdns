#bjdns

一个简陋的带缓存的DNS服务器，用于防止有关部门的DNS污染。

###Version
每个版本更新内容见commits,不再在此更新

###Support
Windows/Linux/OS X

###Depends
Python(>=3)  
python-tkinter    
[Winico](https://github.com/lijiejie/python-flash-trayicons/tree/master/winico0.6)(仅Windows依赖)  
p.s. 打包版已内置以上依赖。

###Usage
####Linux/OS X:
修改本机DNS为127.0.0.1，然后在终端输入  
$sudo python3 bjdns.py  

####Windows:
下载打包版[点我](https://github.com/bieberg0n/bjdns/releases)  
在网络连接的本地连接(或者无线网络)-属性-IPv4里，将首选DNS服务器改为127.0.0.1，然后启动目录中的bjdns.exe。  
任务栏图标右键弹出菜单可退出。  

####P.S.
2016-04-29 加入过滤广告功能,如果不需要这个功能可自行删除ad.txt .  

###Reference
[Python 实现DNS服务器(Pyhon域名解析服务器)](http://blog.csdn.net/trbbadboy/article/details/8093256)  
[Python使用winIco编写一个托盘图标不停闪烁的小程序](http://www.lijiejie.com/python-winico-flash-trayicon/)

###Authors
bjong

###License (MIT)
Copyright (c) 2015-2016 bjong
