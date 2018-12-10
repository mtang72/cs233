#!/usr/bin/env python3
import argparse, socket, multiprocessing, re

def webcrawl(hostnm,port):
	soc = socket.socket()
	try:
		soc.connect((hostnm,port))
	except:
		raise Exception("FUCK")
	links = ['http://www.google.com/index.html']
	while links!=[]:
		#get header
		cmd = 'HEAD {} HTTP/1.1\r\nHost: {}\r\n\r\n'.format(links[-1],hostnm)
		try:
			soc.sendall(cmd.encode())
		except:
			raise Exception('fuck')
		header = ''
		while True:
			chonk = soc.recv(2048)
			header += chonk.decode()
			if chonk[-4:] == b'\r\n\r\n':
				break
		cmd = 'GET'+cmd[4:]
		try:
			soc.sendall(cmd.encode())
		except:
			raise Exception('fuck')
		#skip header to start read
		pos = 0
		while pos<len(header):
			chonk = soc.recv(len(header))
			pos += len(chonk)
		#get size of chonk, then read chonk
		filenm = links[-1].split('/')[-1] if '/' in links[-1] else links[-1]
		f = open(filenm,'wb+')
		while True:
			sz = ''
			while True:
				chonk = soc.recv(1)
				if chonk == b'\n':
					break
				sz += chonk.decode()
			sz = int(sz[:-1],base=16)+2
			if sz == 2:
				break
			pos = 0
			while pos<sz:
				chonk = soc.recv(min(2048,sz-pos))
				pos+=len(chonk)
				f.write(chonk if chonk[-2:]!='\r\n' else chonk[:-2])
			f.seek(-pos+2,1) #must account for removing \r\n from the end
			print(f.read())
			print(sz)
		#links.pop()
		#f.seek(0)
		#print(f.read())
		"""links.extend(filter(lambda x:'html' in x and 'http://' not in x,\
			re.findall(r'(?<=href=)\'|\"[^\'\"]*\'|\"', f.read().decode())))
		print(links)
		f.close()"""
		#Grace is tired
		#Take her home
		break
		#What the fuck is up Richard
	return 0

def multithread():
	pass

if __name__ == '__main__':
	parser = argparse.ArgumentParser(prog='mcrawl',add_help=False)
	parser.add_argument('-n','--max-flows',type=int,dest='nthreads',required=True)
	parser.add_argument('-h','--hostname',dest='hostnm',required=True)
	parser.add_argument('-p','--port',type=int,dest='port',required=True)
	parser.add_argument('-f','--local-directory',dest='dir',required=True)
	args = vars(parser.parse_args())
	if args['nthreads'] > 1:
		multithread()
	webcrawl(args['hostnm'],args['port'])