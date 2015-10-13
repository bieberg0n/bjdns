#!/usr/bin/python3
import socketserver
import re
import struct
import subprocess
import threading
import configparser
import os

__author__ = 'bjong'

# DNS Query
class SinDNSQuery:
    def __init__(self, data):
        i = 1
        self.name = ''
        while True:
            #d = ord(data[i])
            d = data[i]
            if d == 0:
                break;
            if d < 32:
                self.name = self.name + '.'
            else:
                self.name = self.name + chr(d)
            i = i + 1
        self.querybytes = data[0:i + 1]
        (self.type, self.classify) = struct.unpack('>HH', data[i + 1:i + 5])
        self.len = i + 5
    def getbytes(self):
        return self.querybytes + struct.pack('>HH', self.type, self.classify)


# DNS Answer RRS
# this class is also can be use as Authority RRS or Additional RRS 
class SinDNSAnswer:
    def __init__(self, ip):
        self.name = 49164
        self.type = 1
        self.classify = 1
        self.timetolive = 190
        self.datalength = 4
        self.ip = ip
    def getbytes(self):
        res = struct.pack('>HHHLH', self.name, self.type, self.classify, self.timetolive, self.datalength)
        s = self.ip.split('.')
        res = res + struct.pack('BBBB', int(s[0]), int(s[1]), int(s[2]), int(s[3]))
        return res


# DNS frame
# must initialized by a DNS query frame
class SinDNSFrame:
    def __init__(self, data):
        (self.id, self.flags, self.quests, self.answers, self.author, self.addition) = struct.unpack('>HHHHHH', data[0:12])
        self.query = SinDNSQuery(data[12:])
    def getname(self):
        return self.query.name
    def setip(self, ip):
        self.answer = SinDNSAnswer(ip)
        self.answers = 1
        self.flags = 33152
    def getbytes(self):
        res = struct.pack('>HHHHHH', self.id, self.flags, self.quests, self.answers, self.author, self.addition)
        res = res + self.query.getbytes()
        if self.answers != 0:
            res = res + self.answer.getbytes()
        return res


# A UDPHandler to handle DNS query
class SinDNSUDPHandler(socketserver.BaseRequestHandler):
    def send(self,name,dns,socket):
        IP_PTN = re.compile('\d+\.\d+\.\d+\.\d+')
        dnserver = 'fuckgfw'
        if [ x for x in google if name.endswith(x) ]:
            ip = google_ip
            print('google ', end='')

        elif name in cache:
            ip = cache[name]
            print('cache ', end='')

        else:
            for domain in l:
                if name.endswith(domain):
                    dnserver = 'cdnserver'
                    break
            out = subprocess.getoutput('dig {} @{} -p {} +short'.format(name,ds[dnserver][0],ds[dnserver][1]))
            ip = IP_PTN.findall(out)[0] if IP_PTN.findall(out) else '127.0.0.1'
            if ip:
                cache[name] = ip
                with open('cache.txt','a') as f:
                    f.write('{} {}\n'.format(name,ip))

        dns.setip(ip)
        socket.sendto(dns.getbytes(), self.client_address)
        print(name,ip)

        
    def handle(self):
        data = self.request[0].strip()
        dns = SinDNSFrame(data)
        socket = self.request[1]
        #namemap = SinDNSServer.namemap
        if(dns.query.type==1):
            # If this is query a A record, then response it
            name = dns.getname()
            p = threading.Thread(target=self.send,args=(name,dns,socket,))
            p.start()
            #if namemap.__contains__(name):
            #    # If have record, response it
            #    dns.setip(namemap[name])
            #    socket.sendto(dns.getbytes(), self.client_address)
            #elif namemap.__contains__('*'):
            #    # Response default address
            #    dns.setip(namemap['*'])
            #    socket.sendto(dns.getbytes(), self.client_address)
            #else:
            #    # ignore it
            #    socket.sendto(data, self.client_address)
        else:
            # If this is not query a A record, ignore it
            socket.sendto(data, self.client_address)


# DNS Server
# It only support A record query
# user it, U can create a simple DNS server
# class SinDNSServer:
#     def __init__(self):
#         #SinDNSServer.namemap = {}
#         pass
#     #def addname(self, name, ip):
#     #    SinDNSServer.namemap[name] = ip
#     def start(self):
#         HOST, PORT =listen['ip'],listen['port']
#         server = socketserver.UDPServer((HOST, PORT), SinDNSUDPHandler)
#         server.serve_forever()


def start():
    # HOST, PORT =listen['ip'],listen['port']
    server = socketserver.UDPServer((listen['ip'], listen['port']), SinDNSUDPHandler)
    server.serve_forever()


def menu_func(event, x, y):
    if event == 'WM_RBUTTONDOWN':    # Right click tray icon, pop up menu
        menu.tk_popup(x, y)
    #elif event == 'WM_LBUTTONDOWN' and visible == True:    # Right click tray icon, pop up menu
        #change_visible()

# def change_visible():
#     #messagebox.showinfo('msg', 'you clicked say hello button.')
#     global visible
#     visible = not visible
#     whnd = ctypes.windll.kernel32.GetConsoleWindow()   
#     if whnd != 0:   
#         ctypes.windll.user32.ShowWindow(whnd, int(visible))
#         ctypes.windll.kernel32.CloseHandle(whnd) 
    #win32gui.ShowWindow(hd,int(visible))

    
def quit():
    root.quit()
    root.destroy()
    sys.exit()

    
# Now, test it
if __name__ == "__main__":

    dnserver = 'fuckgfw'
    cf = configparser.ConfigParser()
    cf.read('dnserver.conf')
    listen = {
            'ip':cf.get('listen','ip'),
            'port':int(cf.get('listen','port'))
            }
    ds = {
        'fuckgfw':[
                cf.get('fuckgfw','server'),
                cf.get('fuckgfw','port')
                ],
        'cdnserver':[
                cf.get('cdnserver','server'),
                cf.get('cdnserver','port')
                ]
        }
    l = open('cdnlist.txt','r').read().split('\n')
    l.pop()
    cache = open('cache.txt','r').read().split('\n')
    cache.pop()
    cache = { x.split()[0]:x.split()[1] for x in cache }
    google = open('google.txt','r').read().split('\n')
    google.pop()
    google_ip = cf.get('fuckgfw','google_ip')
    # sev = SinDNSServer()
    #sev.addname('www.aa.com', '192.168.0.1')    # add a A record
    #sev.addname('www.bb.com', '192.168.0.2')    # add a A record
    #sev.addname('*', '0.0.0.0') # default address
    if os.name == 'nt':
        #import ctypes
        import sys
        from tkinter import Tk, Menu#,messagebox
        #import win32api, win32gui
        #visible = bool(int(cf.get('listen','visible')))
        #whnd = ctypes.windll.kernel32.GetConsoleWindow()   
        #if whnd != 0:   
        #if not visible:
            #ctypes.windll.user32.ShowWindow(whnd, int(visible))
            #ctypes.windll.kernel32.CloseHandle(whnd) 
        #ct = win32api.GetConsoleTitle()   
        #hd = win32gui.FindWindow(0,ct)   
        #win32gui.ShowWindow(hd,int(visible))
        print(ds)
        root = Tk()
        root.tk.call('package', 'require', 'Winico')
        icon = root.tk.call('winico', 'createfrom', os.path.join(os.getcwd(), 'py.ico'))    # New icon resources
        root.tk.call('winico', 'taskbar', 'add', icon,
                     '-callback', (root.register(menu_func), '%m', '%x', '%y'),
                     '-pos',0,
                     '-text','dnserver')
        menu = Menu(root, tearoff=0)
        #menu.add_command(label='显示/隐藏', command=change_visible)
        menu.add_command(label='退出', command=quit)

        root.withdraw()
        t = threading.Thread(target=sev.start)
        t.setDaemon(True)
        t.start()
        root.mainloop()
    else:
        # sev.start() # start DNS server
        # HOST, PORT = listen['ip'],listen['port']
        # server = socketserver.UDPServer((HOST, PORT), SinDNSUDPHandler)
        # server.serve_forever()
        start()

        # Now, U can use "nslookup" command to test it
        # Such as "nslookup www.aa.com"

