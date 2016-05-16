import socket
from struct import pack, unpack
# import configparser
import os
import time
import threading
import requests
# import queue
#from contextlib import contextmanager
from gevent.server import DatagramServer
# from gevent import socket
from gevent import monkey
monkey.patch_socket()

def inlist(name, dict):
	name = name.split('.')
	name.reverse()
	for i in range(1,len(name)+1):
		_name = list(reversed([ name[j] for j in range(i) ]))
		_name = '.' + '.'.join(_name)
		if dict.get(_name):
			return True
	else:
		return False


def get_data(data,cdn=0):
	s    = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	s.settimeout(2)
	s.sendto(data, ('119.29.29.29', 53))
	data = s.recv(512)
	return data


def get_data_by_tcp(data):
	data = pack('>H', len(data)) + data
	s    = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.settimeout(2)
	s.connect(('160.16.101.80', 5333))
	s.send(data)
	res  = s.recv(512)
	return res[2:]


s = requests.session()
def get_ip_by_openshift(name):
	# ip = s.post('https://mc-bieber.rhcloud.com',data={'n':name}).text
	ip = s.post('http://rss.bjgong.tk',data={'n':name}).text
	return ip

	
def make_data(data, ip):
	#data即请求包
	(id, flags, quests,
	 answers, author, addition) = unpack('>HHHHHH', data[0:12])
	flags_new   = 33152
	answers_new = 1
	res         = pack('>HHHHHH', id, flags_new, quests,
					   answers_new, author, addition)
	
	res        += data[12:]
	
	dns_answer  = {
		'name':49164,
		'type':1,
		'classify':1,
		'ttl':190,
		'datalength':4
		}
	res        += pack('>HHHLH', dns_answer['name'], dns_answer['type'],
					  dns_answer['classify'], dns_answer['ttl'],
					  dns_answer['datalength'])
	
	ip          = ip.split('.')
	ip_bytes    = pack('BBBB', int(ip[0]), int(ip[1]),
					int(ip[2]), int(ip[3]))
	res        += ip_bytes
	
	return res


def get_ip(res, data_len):
	index_0101 = res[data_len:].index(b'\x00\x01\x00\x01')
	ip_bytes   = unpack('BBBB',res[data_len:][index_0101+10:index_0101+14])
	ip         =  '.'.join( [ str(i) for i in ip_bytes ] )
	return ip


def eva(data, client):
	# with lock:
	# while 1:
	# data, client = queue.get()
	list_iter = iter(data[13:])
	name      = ''
	for bit in iter(lambda: next(list_iter), 0):
		name += '.' if bit < 32 else chr(bit)

	type = unpack('>H',data[14+len(name):16+len(name)])
	type = type[0]
	if not type:
		server.sendto(get_data(data), client)

	if name in cache:
		ip = cache[name]
		print(client[0],
			  '[{}]'.format(time.strftime('%Y-%m-%d %H:%M:%S')),
			  '[cache]', name, ip)#, '({})'.format(i) )
		server.sendto(make_data(data, ip), client)

	# elif [ 1 for x in ad if name.endswith(x) or name == x[1:] ]:
	elif inlist(name, ad):
		ip = '127.0.0.1'
		print( client[0],
			   '[{}]'.format(time.strftime('%Y-%m-%d %H:%M:%S')),
			   '[ad]', name, ip)#, '({})'.format(i) )
		server.sendto(make_data(data, ip), client)

	# elif [ 1 for x in google if name.endswith(x) or name == x[1:] ]:
	elif inlist(name, google):
		ip = google_ip
		print( client[0],
			   '[{}]'.format(time.strftime('%Y-%m-%d %H:%M:%S')),
			   '[google]', name, ip)#, '({})'.format(i) )
		server.sendto(make_data(data, ip), client)

	# elif [ 1 for x in cdn_list if name.endswith(x) or name == x[1:] ]:
	elif inlist(name, cdn_list):
		print(client[0],
			  '[{}]'.format(time.strftime('%Y-%m-%d %H:%M:%S')),
			  '[cdn]', name,)# '({})'.format(i) )
		try:
			res = get_data(data,cdn=1)
			# res = get_data_by_tcp(data)
		except socket.timeout:
			# continue
			return
		server.sendto(res, client)
		if 'bjgong.tk' in name:
			try:
				ip = get_ip(res, len(data))
			except ValueError:
				# continue
				return
			cache[name] = ip

	else:
		try:
			resp = get_data_by_tcp(data)
			server.sendto(resp, client)
			ip = get_ip(resp, len(data))
		except (socket.timeout,ValueError):
			# with ignored():
			try:
				ip = get_ip_by_openshift(name)
				server.sendto(make_data(data,ip), client)
			except:
				return

		# ip = unpack('BBBB',data[32+len(name):36+len(name)])
		# ip = '.'.join( [ str(i) for i in ip ] )
		print(client[0],
			  '[{}]'.format(time.strftime('%Y-%m-%d %H:%M:%S')),
			  name, ip)#, '({})'.format(i) )
		cache[name] = ip


server = DatagramServer(('0.0.0.0',53), eva)
def adem():
	# server = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	# server.bind(('0.0.0.0', 53))
	# queue_list = [ queue.Queue() for i in range(16) ]
	# for i in range(16):
	# 	t = threading.Thread(target=eva,args=(queue_list[i],server,i, ))
	# 	t.start()
	# while 1:
	# 	for q in queue_list:
	# 		try:
	# 			data, client = server.recvfrom(512,)
	# 			q.put((data,client))
	# 		except ConnectionResetError:
	# 			continue
	server.serve_forever()


if __name__ == "__main__":

	# cf = configparser.ConfigParser()
	# cf.read('bjdns.conf')
	# listen = {
	# 		'ip':cf.get('listen','ip'),
	# 		'port':int(cf.get('listen','port'))
	# 		}
	# dns = {
	# 	'server':cf.get('dns','server'),
	# 	'port':int(cf.get('dns','port'))
	# 	}
	# google_ip = cf.get('fuckgfw','google_ip')
	google_ip = '64.233.162.83'
	cache = {}

	# cdn_list = open('cdnlist.txt','r').read().split('\n')
	cdn_list = { x:True for x in open('cdnlist.txt','r').read().split('\n') if x}
	# cdn_list.pop()

	# if not os.path.isfile('cache.txt'):
	# 	open('cache.txt','w')
	# cache = open('cache.txt','r').read().split('\n')
	# cache.pop()
	# cache = { x.split()[0]:x.split()[1] for x in cache }
	# with open('cache.txt','w') as f:
	# 	for i in cache:
	# 		f.write('{} {}\n'.format(i,cache[i]))

	google = { x:True for x in open('google.txt','r').read().split('\n') if x}
	# google = open('google.txt','r').read().split('\n')
	# google.pop()

	# ad = open('ad.txt','r').read().split('\n')
	ad = { x:True for x in open('ad.txt','r').read().split('\n') if x} if os.path.isfile('ad.txt') else {}
	# ad.pop()

	adem()
	exit()
	if os.name == 'nt':
		import sys
		from tkinter import Tk, Menu#,messagebox

		def menu_func(event, x, y):
			if event == 'WM_RBUTTONDOWN':	# Right click tray icon, pop up menu
				menu.tk_popup(x, y)


		def quit():
			root.quit()
			root.destroy()
			sys.exit()
				
				
		# print(dns)
		root = Tk()
		root.tk.call('package', 'require', 'Winico')
		icon = root.tk.call('winico', 'createfrom', os.path.join(os.getcwd(), 'py.ico'))	# New icon resources
		root.tk.call('winico', 'taskbar', 'add', icon,
					 '-callback', (root.register(menu_func), '%m', '%x', '%y'),
					 '-pos',0,
					 '-text','bjdns')
		menu = Menu(root, tearoff=0)
		menu.add_command(label='退出', command=quit)

		root.withdraw()
		t = threading.Thread(target=adem)
		t.setDaemon(True)
		t.start()
		root.mainloop()
		
	else:
		adem()
