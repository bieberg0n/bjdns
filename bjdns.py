#coding=utf-8
import socket
from struct import pack, unpack
import os
import time
import threading
import requests
from gevent.server import DatagramServer
import re
#from gevent import socket

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
	# data = pack('>H', len(data)) + data
	# s    = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s    = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	s.settimeout(2)
	s.sendto(data, ('119.29.29.29', 53))
	data = s.recv(512)
	return data
	# s.connect(('114.114.114.114', 53))
	# s.send(data)
	# res  = s.recv(512)
	# return res[2:]


def get_data_by_tcp(data):
	data = pack('>H', len(data)) + data
	s    = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# s.settimeout(5)
	s.connect(('g.bjong.me', 5353))
	s.send(data)
	res  = s.recv(512)
	return res[2:]


s = requests.session()
def get_ip_by_openshift(name):
	# ip = s.post('https://mc-bieber.rhcloud.com',data={'n':name}).text
	ip = s.post('http://bjdns.bjong.me',data={'n':name}).text
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
		'ttl':600,
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


def get_ip_from_resp(res, data_len):
	res = res[data_len:]
	# res_old = res
	# res1 = res[:]
	# while b'\x00\x01\x00\x01' in res:
	# res = res[res.index(b'\xc0\x0c\x00\x01\x00\x01'):]
	p = re.compile(b'\xc0.\x00\x01\x00\x01')
	# print(p.split(res))
	try:
		res = p.split(res)[1]
	except IndexError as e:
		# print(e, res)
		return '127.0.0.1'
	# print(res_old)
	# print(res)
	# print(res1)
	# index_0101 = res[data_len:].index(b'\x00\x01\x00\x01')
	# ip_bytes   = res[data_len].split(b'\x00\x01\x00\x01')[-1]
	# ip_bytes   = unpack('BBBB',res[data_len:][index_0101+10:index_0101+14])
	ip_bytes   = unpack('BBBB',res[6:10])
	# ip_bytes = res[-4:]
	ip         =  '.'.join( [ str(i) for i in ip_bytes ] )
	# print(ip_bytes,res[data_len:][index_0101+10:])
	return ip


def get_ip(data, name):
	# try:
	resp = get_data_by_tcp(data)
	ip = get_ip_from_resp(resp, len(data))
	# except (socket.timeout,ValueError,ConnectionResetError) as e:
	# 	print(e)
	# 	try:
	# 		ip = get_ip_by_openshift(name)
	# 	except:
	# 		return

	return ip


def eva(data, client):
	global cache, cache_date
	list_iter = iter(data[13:])
	name      = ''
	for bit in iter(lambda: next(list_iter), 0):
		name += '.' if bit < 32 else chr(bit)

	type = unpack('>H',data[14+len(name):16+len(name)])
	type = type[0]
	if not type:
		server.sendto(get_data(data), client)
		return

	# if int( time.time() ) - cache_date > 259200:
	# 	cache = {}
	# 	cache_date = int( time.time() )
	# 	print('cache flush')
	
	if name in cache:
		ip = cache[name]
		print(client[0],
			  '[{}]'.format(time.strftime('%Y-%m-%d %H:%M:%S')),
			  '[cache]', name, ip)#, '({})'.format(i) )
		server.sendto(make_data(data, ip), client)
		if inlist(name, cdn_list) or 'bjong.me' in name:
			res = get_data(data,cdn=1)
			ip_new = get_ip_from_resp(res, len(data))
		else:
			ip_new = get_ip(data, name)
		# print('now ip:', ip_new)
		if ip != ip_new:
			cache[name] = ip_new

	elif inlist(name, ad):
		ip = '127.0.0.1'
		print( client[0],
			   '[{}]'.format(time.strftime('%Y-%m-%d %H:%M:%S')),
			   '[ad]', name, ip)#, '({})'.format(i) )
		server.sendto(make_data(data, ip), client)

	elif inlist(name, google):
		ip = google_ip
		print( client[0],
			   '[{}]'.format(time.strftime('%Y-%m-%d %H:%M:%S')),
			   '[google]', name, ip)#, '({})'.format(i) )
		server.sendto(make_data(data, ip), client)

	elif inlist(name, cdn_list):
		print(client[0],
			  '[{}]'.format(time.strftime('%Y-%m-%d %H:%M:%S')),
			  '[cdn]', name,)# '({})'.format(i) )
		try:
			res = get_data(data,cdn=1)
		except socket.timeout as e:
			print(e)
			return
		server.sendto(res, client)
		ip = get_ip_from_resp(res, len(data))
		cache[name] = ip

	elif 'bjong.me' in name:
		res = get_data(data,cdn=1)
		server.sendto(res, client)
		print(client[0],
			  '[{}]'.format(time.strftime('%Y-%m-%d %H:%M:%S')),
			  '[cdn]', name,)# '({})'.format(i) )
		try:
			ip = get_ip_from_resp(res, len(data))
		except ValueError:
			return
		cache[name] = ip

	else:
		ip = get_ip(data, name)
		server.sendto(make_data(data,ip), client)
		print(client[0],
			  '[{}]'.format(time.strftime('%Y-%m-%d %H:%M:%S')),
			  name, ip)#, '({})'.format(i) )
		cache[name] = ip


if os.name == 'ntx':
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.bind( ('0.0.0.0', 53) )
	server = s
else:
	from gevent import monkey
	monkey.patch_socket()
	server = DatagramServer(('0.0.0.0',53), eva)


def adem_thread():
	while 1:
		try:
			data, client = s.recvfrom(512)
			threading.Thread(target=eva,args=(data, client,)).start()
		except ConnectionResetError:
			pass


def adem():
	server.serve_forever()


if __name__ == "__main__":

	google_ip = '64.233.162.83'
	cache = {}
	# cache_date = int( time.time() )

	cdn_list = { x:True for x in open('cdnlist.txt','r').read().split('\n') if x}

	google = { x:True for x in open('google.txt','r').read().split('\n') if x}
	ad = { x:True for x in open('ad.txt','r').read().split('\n') if x} if os.path.isfile('ad.txt') else {}

	#adem()
	#exit()
	if os.name == 'nt':
		adem()
		exit()

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
		t = threading.Thread(target=adem_thread)
		t.setDaemon(True)
		t.start()
		root.mainloop()

	else:
		adem()
