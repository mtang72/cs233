#i'm sorry to all the fans but i would seriously rather use sublime text than vim
import argparse,sys,socket,re
class ConnectionError(Exception):
	pass

def ftp_nonpar(file,hostnm,user,pwd,port,out):
	addr = socket.gethostbyname(hostnm)
	#soc.bind(('',port))
	soc1 = socket.socket()
	soc2 = socket.socket()
	soc1.connect((hostnm,port))
	while True:
		rec = soc1.recv(256)
		if not rec:
			break
		msg = rec.decode().strip()
		code,snd = msg[0:3], "" #to get the message code
		if code=="220": #username ask
			snd = "USER "+user
		if code=="331": #password ask
			snd = "PASS "+pwd
		if code=="430" or code=="530": #invalid username/pass
			raise ValueError("invalid username/password")
		if code=="550": #invalid filename
			raise ValueError("invalid filename")
		if code=="421": #timeout
			raise ConnectionError()
		if code=="150": #file sending
			with open(file, "wb") as f:
				while True:
					chunk = soc2.recv(2048)
					if not chunk:
						break
					f.write(chunk)
			print("File transfer successful.")
			snd = "QUIT"
		if code=="230" or code=="425": #login successful/select PASV
			snd = "PASV"
		if code=="227": #PASV successful
			hostaddr = ".".join(re.search(r"\(\d{1,3},\d{1,3},\d{1,3},\d{1,3}",msg).group()[1:].split(","))
			p1, p2 = map(int,re.search(r"\d{0,5},\d{0,5}\)",msg).group()[:-1].split(","))
			soc2.connect((hostaddr, p1*256+p2))
			snd = "RETR "+file
		data = (snd+"\n").encode()
		if out:
			print("S->C: {}\nC->S: {}".format(msg,snd), file=out)
		soc1.sendall(data)
	soc1.close()
	soc2.close()
	return "Connection closed."


if __name__ == "__main__":
	parser = argparse.ArgumentParser(prog="pftp")
	parser.add_argument("-s",required=True,metavar="hostname",dest="hostname")
	parser.add_argument("-f",required=True,metavar="file",dest="file")
	parser.add_argument("-v", "--version",action="version",version="%(prog)s v0.1 by Michael Tang (mtang72)")
	parser.add_argument("-p","--port",type=int,metavar="port",default=21)
	parser.add_argument("-n","--username",metavar="user",default="anonymous")
	parser.add_argument("-P","--password",metavar="password",default="user@localhost.localnet")
	parser.add_argument("-l","--log",metavar="logfile",default=None)
	args = vars(parser.parse_args())
	file = args['file']
	hostnm = args['hostname']
	if args['log']:
		log = open(args['log'],'w') if args['log']!='-' else sys.stdout
	else:
		log = None
	pwd = args['password']
	port = args['port']
	user = args['username']
	print(ftp_nonpar(file,hostnm,user,pwd,port,log))
	if log and log!=sys.stdout:
		log.close()