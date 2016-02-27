import socket
from struct import pack, unpack
import configparser
import os
import threading

def get_data(data,cdn=0):
	s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	if cdn:
		s.sendto(data, (dns['server'],dns['port']))
	else:
		s.sendto(data, ('208.67.220.220', 5353))
	data = s.recv(512)
	return data


def get_data_by_tcp(data):
	data = pack('>H', len(data)) + data
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect(('208.67.220.220', 53))
	s.send(data)
	res = s.recv(512)
	return res[2:]


def make_data(data, ip):
	(id, flags, quests,
	 answers, author, addition) = unpack('>HHHHHH', data[0:12])
	flags_new = 33152
	answers_new = 1
	res = pack('>HHHHHH', id, flags_new, quests,
			   answers_new, author, addition)
	
	res += data[12:]
	
	dns_answer = {
		'name':49164,
		'type':1,
		'classify':1,
		'ttl':190,
		'datalength':4
		}
	res += pack('>HHHLH', dns_answer['name'], dns_answer['type'],
					  dns_answer['classify'], dns_answer['ttl'],
					  dns_answer['datalength'])
	
	ip = ip.split('.')
	ip_bytes = pack('BBBB', int(ip[0]), int(ip[1]),
					int(ip[2]), int(ip[3]))
	res += ip_bytes
	
	return res


def get_ip(res, data_len):
	index_0101 = res[data_len:].index(b'\x00\x01\x00\x01')
	ip_bytes = unpack('BBBB',res[data_len:][index_0101+10:index_0101+14])
	ip =  '.'.join( [ str(i) for i in ip_bytes ] )
	return ip


def eva(data, client, server):
	list_iter = iter(data[13:])
	name = ''
	for bit in iter(lambda: next(list_iter), 0):
		name += '.' if bit < 32 else chr(bit)
	
	type = unpack('>H',data[14+len(name):16+len(name)])
	type = type[0]
	if not type:
		server.sendto(get_data(data), client)
		
	if [ 1 for x in google if name.endswith(x) or name == x[1:] ]:
		ip = google_ip
		print('google', name, ip)
		server.sendto(make_data(data, ip), client)

	elif name in cache:
		ip = cache[name]
		print('cache', name, ip)
		server.sendto(make_data(data, ip), client)

	else:
		if [ 1 for i in cdn_list if name.endswith(i) or name == i[1:] ]:
			print('cdn', name)
			# server.sendto(get_data(data,cdn=1), client)
			res = get_data(data,cdn=1)

		# res = get_data_by_tcp(data)
		else:
			res = get_data(data)
			
		server.sendto(res, client)
		
		# ip = unpack('BBBB',data[32+len(name):36+len(name)])
		# ip = '.'.join( [ str(i) for i in ip ] )
		ip = get_ip(res, len(data))
		print(name, ip)
		cache[name] = ip
		# with open('cache.txt','a') as f:
		# 	f.write('{} {}\n'.format(name,ip))
	# exit()


def adem():
	server = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	server.bind((listen['ip'],listen['port']))
	while 1:
		try:
			data, client = server.recvfrom(512,)
		except ConnectionResetError:
			continue
		t = threading.Thread(target=eva,args=(data, client, server ))
		t.start()

	
if __name__ == "__main__":

	cf = configparser.ConfigParser()
	cf.read('bjdns.conf')
	listen = {
			'ip':cf.get('listen','ip'),
			'port':int(cf.get('listen','port'))
			}
	dns = {
		'server':cf.get('dns','server'),
		'port':int(cf.get('dns','port'))
		}
	google_ip = cf.get('fuckgfw','google_ip')
	
	cdn_list = open('cdnlist.txt','r').read().split('\n')
	cdn_list.pop()

	# if not os.path.isfile('cache.txt'):
	# 	open('cache.txt','w')
	# cache = open('cache.txt','r').read().split('\n')
	# cache.pop()
	# cache = { x.split()[0]:x.split()[1] for x in cache }
	# with open('cache.txt','w') as f:
	# 	for i in cache:
	# 		f.write('{} {}\n'.format(i,cache[i]))
	cache = {}

	google = open('google.txt','r').read().split('\n')
	google.pop()

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
				
				
		print(dns)
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
