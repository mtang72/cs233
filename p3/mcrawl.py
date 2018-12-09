#!/usr/bin/env python3
import argparse, socket, multiprocessing
from html.parser import HTMLParser

class fuckyourmom(HTMLParser):
	def handle_data():
		pass

def webcrawl(hostnm,port):
	soc = socket.socket()
	try:
		soc.connect((hostnm,port))
	except:
		raise Exception("FUCK")
	while True:
		cmd = 'GET /index.html HTTP/1.1\r\nHost: eychtipi.cs.uchicago.edu\r\n\r\n'
		try:
			soc.sendall((cmd).encode())
		except:
			raise Exception("fuck")
		pos = 0
		filesize = 10000
		f = open("out.txt", "wb+")
		while pos<filesize:
			chunk = soc.recv(min(filesize-pos,4096))
			pos += len(chunk)
			if not chunk:
				break
			f.write(chunk)
			#I'm Michael
		f.seek(0)
		print(f.read())
		f.close()
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