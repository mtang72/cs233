#i'm sorry to all the fans but i would seriously rather use sublime text than vim
import argparse,sys,socket,re,threading,os,tempfile

"""def err(file, log, threads): #handle temp file deletion
	if threads:
		for i in range(threads):
			try:
				os.remove(str(i)+"-"+file)
			except TypeError:
				print(file,log,threads)
	else:
		try:
			os.remove(file)
		except FileNotFoundError:
			pass
	if log and log!=sys.stdout:
		log.close()
	raise Exception("7: Generic error")"""


def ftp(file,hostnm,user,pwd,port,out,inter=None,posn=None): #inter,pos should be (#intervals, position) when it exists
	addr = socket.gethostbyname(hostnm)
	#soc.bind(('',port))
	soc1 = socket.socket()
	soc2 = socket.socket()
	soc1.connect((hostnm,port))
	filesize = 0
	while True:
		rec = soc1.recv(256)
		if not rec:
			break
		msg = rec.decode().strip()
		if out:
			print(("T{}: ".format(posn) if posn!=None else "")+"S->C: ",msg, file=out)
		code,snd = msg[0:3], "" #to get the message code
		if code=="500": #incorrect command
			raise Exception("5: Command not implemented by server")
		if code=="501":
			raise Exception("4: Syntax error in client request")
		if code=="220": #username ask
			snd = "USER "+user
		if code=="331": #password ask
			snd = "PASS "+pwd
		if code=="430" or code=="530": #invalid username/pass
			raise Exception("2: Authentication failed")
		if code=="550": #invalid filename
			raise Exception("3: File not found")
		if code=="421": #timeout
			raise Exception("1: Can't connect to server")
		if code=="150": #file sending
			filesize //= inter if inter else 1
			with open(file, "wb") as f:
				pos = 0
				while pos<filesize:
					chunk = soc2.recv(min(filesize-pos,4096))
					pos += len(chunk)
					#print("pos: {}  last packet size: {}".format(pos,len(chunk)))
					if not chunk:
						break
					f.write(chunk)
				while (posn!=None and inter!=None) and posn==inter-1: #reading leftover bytes
					chunk = soc2.recv(1024)
					if not chunk:
						break
					f.write(chunk)
		if code=="226": #transfer complete
			snd = "QUIT"
		if code=="230" or code=="425": #login successful/select PASV
			snd = "PASV"
		if code=="227": #PASV successful
			hostaddr = ".".join(re.search(r"\(\d{1,3},\d{1,3},\d{1,3},\d{1,3}",msg).group()[1:].split(","))
			p1, p2 = map(int,re.search(r"\d{0,5},\d{0,5}\)",msg).group()[:-1].split(","))
			soc2.connect((hostaddr, p1*256+p2))
			snd = "SIZE "+file
		if code=="213": #size of file received
			filesize = int(msg.split()[1])
			snd = "TYPE I"
		if code=="200": #binary switch successful
			pos = (filesize//inter)*posn if inter else 0
			snd = "REST {}".format(pos)
		if code=="350": #restart position accepted
			snd = "RETR "+file
		data = (snd+"\n").encode()
		if out:
			print(("T{}: ".format(posn) if posn!=None else "")+"C->S: ",snd, file=out)
		soc1.sendall(data)
	soc1.close()
	soc2.close()
	return 0

def threadft(cmds, port, log): #multithread downloading
	threads = []
	for i in range(len(cmds)):
		user, pwd = re.search(r"(?<=ftp://).*:.*(?=@)",cmds[i]).group().split(":")
		hostnm = re.search(r"(?<=@).*(?=/)",cmds[i]).group()
		file = re.search(r"/.*$",cmds[i][6:]).group()[1:]
		threads.append(threading.Thread(target=ftp, args=(file,hostnm,user,pwd,port,log),kwargs={'inter':len(cmds),'posn':i}))
	for thread in threads:
		thread.start()
	for thread in threads:
		thread.join()
	#file = str(posn)+"-"+file
	with open("0-"+file,"ab") as f:
		for i in range(1,len(cmds)):
			try:
				with open(str(i)+"-"+file,"rb") as f1:
					f.write(f1.read())
				os.remove(str(i)+"-"+file)
			except FileNotFoundError:
				err(file, log, len(cmds))
		try:
			os.remove(file)
		except FileNotFoundError:
			pass
		os.rename("0-"+file,file)
	return 0

if __name__ == "__main__":
	parser = argparse.ArgumentParser(prog="pftp")
	parser.add_argument("-s",metavar="hostname",dest="hostname")
	parser.add_argument("-f",metavar="file",dest="file")
	parser.add_argument("-v", "--version",action="version",version="%(prog)s v0.1 by Michael Tang (mtang72)")
	parser.add_argument("-p","--port",type=int,metavar="port",default=21)
	parser.add_argument("-n","--username",metavar="user",default="anonymous")
	parser.add_argument("-P","--password",metavar="password",default="user@localhost.localnet")
	parser.add_argument("-l","--log",metavar="logfile")
	parser.add_argument("-t","--thread",metavar="cfg_file",dest="cfg")
	args = vars(parser.parse_args())
	if not args['cfg'] and not (args['hostname'] or args['file']):
		parser.error("-s, -f required if -t not given")
	file = args['file']
	hostnm = args['hostname']
	if args['log']:
		log = open(args['log'],'w') if args['log']!='-' else sys.stdout
	else:
		log = None
	pwd = args['password']
	port = args['port']
	user = args['username']
	if args['cfg']: #read config file, override parameters and enter multithread mode
		with open(args['cfg'],'r') as f:
			cmds = f.read().strip().split('\n')
			try:
				if threadft(cmds, port, log) == 0:
					print("0: Operation successfully completed")
			except KeyboardInterrupt:
				err(file,log,len(cmds))
	else:
		try:
			if ftp(file,hostnm,user,pwd,port,log) == 0:
				print("0: Operation successfully completed")
		except KeyboardInterrupt:
			err(file,log,None)
	if log and log!=sys.stdout:
		log.close()