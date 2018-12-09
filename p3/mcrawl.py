#!/usr/bin/env python3
import argparse, socket, multiprocessing

def webcrawl(hostnm,port):
	soc = socket.socket()
	try:
		soc.connect((hostnm,port))
	except:
		raise Exception("FUCK")
	while True:
		total = ''
		while True:
			line = input()
			if line.strip('\n') == '':
				break
			total += line
		print(total)
		try:
			soc.sendall((total+'\r\n\r\n').encode())
		except:
			raise Exception("fuck")
		rec = soc.recv(256)
		if not rec: #just in case
			raise Exception("1: Can't connect to server")
		msg = rec.decode().strip()
		print(msg)
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