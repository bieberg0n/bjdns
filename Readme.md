#bjdns

一个简陋的带缓存的DNS服务器，用于防止有关部门的DNS污染。

###Version
[v0.4]  
重构;  
不缓存cdnlist里的域名;  
使用tcp发dns请求。

[v0.3]

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
已用cxfreeze打包成exe,见bjdns.7z。  
下载bjdns.7z,解压。  
在网络连接的本地连接(或者无线网络)-属性-IPv4里，将首选DNS服务器改为127.0.0.1，然后启动目录中的bjdns.exe。  
任务栏图标右键弹出菜单可退出。  

####P.S.
可在bjdns.conf中将8.8.8.8修改为别的更快的DNS服务器。移动连8.8.8.8比较快，电信不快。
若要手动清除缓存，清空cache.txt里面的内容并重开bjdns即可。

###Reference
[Python 实现DNS服务器(Pyhon域名解析服务器)](http://blog.csdn.net/trbbadboy/article/details/8093256)  
[Python使用winIco编写一个托盘图标不停闪烁的小程序](http://www.lijiejie.com/python-winico-flash-trayicon/)

###Authors
bjong

###License (MIT)
Copyright (c) 2015 bjong
