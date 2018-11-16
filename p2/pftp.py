#i'm sorry to all the fans but i would seriously rather use sublime text than vim
import argparse,sys,socket

def ftp_nonpar(file,hostnm,user,pwd,port,out=sys.stdout):
	addr = socket.gethostbyname(hostnm)
	#soc.bind(('',port))
	with socket.socket() as soc:
		soc.connect((hostnm,port))
		count = 0
		while True:
			count+=1
			print("loop ",count)
			soc.sendall(input().encode())
			reply = soc.recv(256)
			if not reply:
				break
			print(reply.decode())



if __name__ == "__main__":
	parser = argparse.ArgumentParser(prog="pftp")
	parser.add_argument("-s",required=True,metavar="hostname",dest="hostname")
	parser.add_argument("-f",required=True,metavar="file",dest="file")
	parser.add_argument("-v", "--version",action="version",version="%(prog)s v0.1 by Michael Tang (mtang72)")
	parser.add_argument("-p","--port",type=int,metavar="port",default=21)
	parser.add_argument("-n","--username",metavar="user",default="anonymous")
	parser.add_argument("-P","--password",metavar="password",default="user@localhost.localnet")
	parser.add_argument("-l","--log",metavar="logfile")
	args = vars(parser.parse_args())
	file = args['file']
	hostnm = args['hostname']
	log = args['log']
	pwd = args['password']
	port = args['port']
	user = args['username']
	ftp_nonpar(file,hostnm,user,pwd,port)