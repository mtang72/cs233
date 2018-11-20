#!/usr/bin/env python3
#i'm sorry to all the fans but i would seriously rather use sublime text than vim
import argparse,sys,socket,re,threading,os,tempfile

def ftp(filenm,file,hostnm,user,pwd,port,out,inter=None,posn=None,results=None): 
#inter,pos should be (#intervals, position) when it exists
#results is a list to document the amount of threads that successfully return
	addr = socket.gethostbyname(hostnm)
	soc1 = socket.socket()
	soc2 = socket.socket()
	soc1.connect((hostnm,port))
	filesize = 0
	while True:
		try:
			rec = soc1.recv(256)
		except socket.timeout:
			raise Exception("1: Can't connect to server")
		if not rec: #just in case
			break
		msg = rec.decode().strip()
		if out:
			print(("T{}: ".format(posn+1) if posn!=None else "")+"S->C: ",msg, file=out)
		code,snd = msg[0:3], "" #to get the message code
		if code=="221": #goodbye
			break
		if code=="500": #incorrect command
			raise Exception("5: Command not implemented/Operation not allowed")
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
		if code=="421" or code=="426": #timeout
			raise Exception("1: Can't connect to server")
		if code=="150": #file sending
			filesize //= inter if inter else 1
			pos = 0
			while pos<filesize:
				chunk = soc2.recv(min(filesize-pos,4096))
				pos += len(chunk)
				if not chunk:
					break
				file.write(chunk)
			while (posn!=None and inter!=None) and posn==inter-1: #reading leftover bytes
				chunk = soc2.recv(1024)
				if not chunk:
					break
				file.write(chunk)
		if code=="226": #transfer complete
			snd = "QUIT"
		if code=="230" or code=="425": #login successful/select PASV
			snd = "PASV"
		if code=="227": #PASV successful
			hostaddr = ".".join(re.search(r"\(\d{1,3},\d{1,3},\d{1,3},\d{1,3}",msg).group()[1:].split(","))
			p1, p2 = map(int,re.search(r"\d{0,5},\d{0,5}\)",msg).group()[:-1].split(","))
			soc2.connect((hostaddr, p1*256+p2))
			snd = "SIZE "+filenm
		if code=="213": #size of file received
			filesize = int(msg.split()[1])
			snd = "TYPE I"
		if code=="200": #binary switch successful
			pos = (filesize//inter)*posn if inter else 0
			snd = "REST {}".format(pos)
		if code=="350": #restart position accepted
			snd = "RETR "+filenm
		data = (snd+"\n").encode()
		if out:
			print(("T{}: ".format(posn+1) if posn!=None else "")+"C->S: ",snd, file=out)
		soc1.sendall(data)
	soc1.close()
	soc2.close()
	if results!=None:
		results.append(0)
	return 0

def threadft(cmds, port, log): #multithread downloading
	threads, tmpfiles, results = [], [], []
	for i in range(len(cmds)):
		user, pwd = re.search(r"(?<=ftp://).*:.*(?=@)",cmds[i]).group().split(":")
		hostnm = re.search(r"(?<=@).*(?=/)",cmds[i]).group()
		filenm = re.search(r"/.*$",cmds[i][6:]).group()
		tmpfiles.append(tempfile.TemporaryFile())
		threads.append(threading.Thread(target=ftp, args=(filenm,tmpfiles[i],hostnm,user,pwd,port,log),\
			kwargs={'inter':len(cmds),'posn':i,'results':results}))
	for thread in threads:
		thread.start()
	for thread in threads:
		thread.join()
	if len(results) != len(threads):
		raise Exception("6: Thread generic failure")
	filenm = re.search(r'[^/]*$',filenm).group() #take away directories so local file will be written in root
	with open(filenm,"wb") as f:
		for tmpfile in tmpfiles:
			tmpfile.seek(0)
			f.write(tmpfile.read())
			tmpfile.close()
	return 0

if __name__ == "__main__":
	parser = argparse.ArgumentParser(prog="pftp")
	parser.add_argument("-s",metavar="hostname",dest="hostname")
	parser.add_argument("-f",metavar="file",dest="filenm")
	parser.add_argument("-v", "--version",action="version",version="%(prog)s v0.1 by Michael Tang (mtang72)")
	parser.add_argument("-p","--port",type=int,metavar="port",default=21)
	parser.add_argument("-n","--username",metavar="user",default="anonymous")
	parser.add_argument("-P","--password",metavar="password",default="user@localhost.localnet")
	parser.add_argument("-l","--log",metavar="logfile")
	parser.add_argument("-t","--thread",metavar="cfg_file",dest="cfg")
	args = vars(parser.parse_args())
	if not args['cfg'] and not (args['hostname'] or args['filenm']):
		if len(sys.argv) == 1:
			parser.print_help()
			sys.exit()
		parser.error("-s, -f required if -t not given")
	filenm = args['filenm']
	hostnm = args['hostname']
	if hostnm and '/' in hostnm: #if directories in hostnm
		direc = re.search(r'/.*$',hostnm[6:]).group()
		filenm = direc + ('/' if direc[-1]!='/' else '') + filenm
		hostnm = re.search(r'(?<=ftp://).*(?=/)',hostnm).group()
		print(filenm,hostnm)
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
			if threadft(cmds, port, log) == 0:
				print("0: Operation successfully completed")
	else:
		with tempfile.TemporaryFile() as file:
			if ftp(filenm,file,hostnm,user,pwd,port,log) == 0:
				filenm = re.search(r'[^/]*$',filenm).group() #take away directories so local file will be written in root
				with open(filenm,"wb") as f:
					file.seek(0)
					f.write(file.read())
				print("0: Operation successfully completed")
	if log and log!=sys.stdout:
		log.close()