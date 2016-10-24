#!/usr/bin/env python3
#coding=utf-8

# copyright 2016 bjong

# import socket
from struct import pack, unpack
import sys
import os
import time
# import socks
from bjdns import geventsocks
import json
from gevent.server import DatagramServer
import re
from gevent import socket
# from gevent import monkey
# monkey.patch_socket()

def inlist(name, dict_):
	name = name.split('.')
	name.reverse()
	for i in range(1,len(name)+1):
		name_ = list(reversed([ name[j] for j in range(i) ]))
		name_ = '.' + '.'.join(name_)
		if dict_.get(name_):
			return True
	else:
		return False


def get_data(data,cdn=0):
	# data = pack('>H', len(data)) + data
	# s    = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s    = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	# s.settimeout(2)
	s.sendto(data, ('119.29.29.29', 53))
	data = s.recv(512)
	return data
	# s.connect(('114.114.114.114', 53))
	# s.send(data)
	# res  = s.recv(512)
	# return res[2:]


def get_data_by_tcp(data):
	# print('get_data_by_tcp')
	data = pack('>H', len(data)) + data
	# s    = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# s = geventsocks.socksocket()
	s = socket.socket()
	geventsocks.connect(s, ('8.8.8.8',53) )
	s.send(data)
	# res = b''
	# for buf in iter(lambda:s.recv(1024),b''):
	# 	print('buf: ', buf)
	res = s.recv(512)
	length = unpack('>H', res[:2])[0]
	# print(length)
	if length <= len(res) - 2:
		pass
	else:
		while len(res) - 2 < length:
			res += s.recv(512)
	s.close()
	# print('get_data_by_tcp over')
	return res[2:]


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
	p = re.compile(b'\xc0.\x00\x01\x00\x01')
	# try:
	res = p.split(res)[1]
	# except IndexError:
	# 	raise Exception('get ip fail')
	# 	return
	ip_bytes   = unpack('BBBB',res[6:10])
	ip         =  '.'.join( [ str(i) for i in ip_bytes ] )
	return ip


# def get_ip(data, name):
# 	resp = get_data_by_tcp(data)
# 	ip = get_ip_from_resp(resp, len(data))
# 	return ip


def eva(data, client):
	list_iter = iter(data[13:])
	name      = ''
	for bit in iter(lambda: next(list_iter), 0):
		name += '.' if bit < 32 else chr(bit)

	type = unpack('>H',data[14+len(name):16+len(name)])
	type = type[0]
	if not type:
		server.sendto(get_data(data), client)
		return

	if name in cache:
		# print('cache')
		ip = cache[name]
		print(client[0],
			  '[{}]'.format(time.strftime('%Y-%m-%d %H:%M:%S')),
			  '[cache]', name, ip)
		server.sendto(make_data(data, ip), client)
		if inlist(name, cdn_list):
			res = get_data(data,cdn=1)
			ip_new = get_ip_from_resp(res, len(data))
		else:
			resp = get_data_by_tcp(data)
			ip_new = get_ip_from_resp(resp, len(data))
		if ip != ip_new:
			cache[name] = ip_new

	elif inlist(name, ad):
		ip = '127.0.0.1'
		print( client[0],
			   '[{}]'.format(time.strftime('%Y-%m-%d %H:%M:%S')),
			   '[ad]', name, ip)
		server.sendto(make_data(data, ip), client)

	elif inlist(name, google):
		ip = google_ip
		print( client[0],
			   '[{}]'.format(time.strftime('%Y-%m-%d %H:%M:%S')),
			   '[google]', name, ip)
		server.sendto(make_data(data, ip), client)

	elif inlist(name, cdn_list):
		print(client[0],
			  '[{}]'.format(time.strftime('%Y-%m-%d %H:%M:%S')),
			  '[cdn]', name,)
		# try:
		res = get_data(data,cdn=1)
		# except socket.timeout as e:
		# 	print(e)
		# 	return
		server.sendto(res, client)
		ip = get_ip_from_resp(res, len(data))
		cache[name] = ip

	else:
		# ip = get_ip(data, name)
		resp = get_data_by_tcp(data)
		ip = get_ip_from_resp(resp, len(data))
		server.sendto(make_data(data,ip), client)
		print(client[0],
			  '[{}]'.format(time.strftime('%Y-%m-%d %H:%M:%S')),
			  name, ip)
		cache[name] = ip


def adem_thread():
	while 1:
		try:
			data, client = s.recvfrom(512)
			threading.Thread(target=eva,args=(data, client,)).start()
		except ConnectionResetError:
			pass


def adem():
	server.serve_forever()


def main():
	global server, google_ip, cache, cdn_list, google, ad

	if os.name == 'nt':
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.bind( ('0.0.0.0', 53) )
		server = s
	else:
		server = DatagramServer(('0.0.0.0',53), eva)

	google_ip = '64.233.162.83'
	cache = {}

	cdn_list = { x:True for x in open('bjdns/cdnlist.txt','r').read().split('\n') if x}

	google = { x:True for x in open('bjdns/google.txt','r').read().split('\n') if x}
	ad = { x:True for x in open('bjdns/ad.txt','r').read().split('\n') if x} if os.path.isfile('ad.txt') else {}

	if len(sys.argv) >= 2:
		json_dir = sys.argv[1]
	else:
		json_dir = 'bjdns/bjdns.json'
	json_str = open(json_dir).read()
	json_dict = json.loads(json_str)
	ss_ip, ss_port = json_dict['socks5_server'].split(':')
	geventsocks.set_default_proxy(ss_ip, int(ss_port))

	if os.name == 'nt':
		# adem()
		# exit()

		import threading
		from tkinter import Tk, Menu#,messagebox

		def menu_func(event, x, y):
			if event == 'WM_RBUTTONDOWN':	# Right click tray icon, pop up menu
				menu.tk_popup(x, y)


		def quit():
			root.quit()
			root.destroy()
			sys.exit()
				
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
		# adem_thread()

if __name__ == '__main__':
	main()
