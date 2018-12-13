#!/usr/bin/env python3
import argparse, socket, multiprocessing as mp, re, os, tempfile, time, collections, ctypes

def reconnect(sock,hostnm,port,globalcookie):
	print("reconnectin")
	sock.close()
	sock = socket.socket()
	#sock.settimeout(5)
	try:
		sock.connect((hostnm,port))
	except:
		raise Exception('FUCK')
	if globalcookie:
		with globalcookie.get_lock():
			globalcookie.value = b''
	return sock

def linkfromglobal(glob,fin,lock):
	start = time.time()
	upcoming = None
	while upcoming==None and time.time()-start<1: #i hate this so much but i see no other solution
		try:
			upcoming = glob.pop()
		except IndexError:
			pass
		lock.acquire()
		if not upcoming or (upcoming and upcoming in fin):
			upcoming = None
		else:
			fin.append(upcoming)
		lock.release()
	return upcoming

def webcrawl(hostnm,port,direc,globalcookie=None,linkqueue=None,lock=None, globalfinished=None, pid=None):
	soc = socket.socket()
	#soc.settimeout(5)
	try:
		soc.connect((hostnm,port))
	except:
		raise Exception("FUCK")
	links = []
	while linkqueue!=None and links==[]: #ISSUE: what if there are no more files left to take?
		upcoming = linkfromglobal(linkqueue,globalfinished,lock)
		if not upcoming:
			break
		links.append(upcoming)	
	if linkqueue==None:
		links = ['/index.html']
	backoff = 1
	cookie = ''
	sz = b''
	#ok ok ok ok ok alright alright alright ok
	files = {}
	finishedlinks = []
	del_crap = lambda x:x and '#' not in x and not (('http://' in x or 'https://' in x)\
		and re.search(r'(?<=://)[^/]*',x).group()!=hostnm) #for link cleaning later
	while links!=[]:
		cookie = globalcookie.value.decode() if globalcookie!=None else cookie
		#print("pid {}: {} vs global {}".format(pid,cookie,globalcookie.value.decode() if globalcookie!=None else None))
		"""if globalfinished!=None:
			print(globalfinished,linkqueue,links)
		else:
			print(finishedlinks,links)"""
		looprest = False #better way to reset loop

		#file handling
		files[links[-1]] = tempfile.TemporaryFile()
		f = files[links[-1]]
		dirnm = '/'.join(links[-1].split('/')[:-1]) if '/' in links[-1] else ''

		#get header
		cmd = 'GET {} HTTP/1.1\r\nHost: {}\r\n\r\n'.format(links[-1],hostnm)
		if cookie:
			cmd = cmd[:-2] + 'Cookie: ' + cookie + '\r\n\r\n'
		try:
			soc.sendall(cmd.encode())
		except:
			raise Exception('fuck')
		header = b''
		while True:
			try:
				rec = soc.recv(512)
			except:
				soc = reconnect(soc,hostnm,port,globalcookie)
				cookie = ''
				looprest = True
				break
			header += rec
			if b'\r\n\r\n' in header:
				break
		if looprest:
			continue

		#pick out header and initial parts of file leftover from header read
		head_end = header.index(b'\r\n\r\n')
		post_head = header[head_end+4:]
		header = header[:head_end].decode()

		#obviously, to determine if it's chonkytime or not
		encoding_type = re.search(r'(?<=Transfer-Encoding:).*',header,re.IGNORECASE)
		chonkytime = encoding_type!=None and re.match(r'chunked',encoding_type.group().strip(),re.IGNORECASE)!=None
		firstround = False
		if not chonkytime:
			clength = re.search(r'(?<=Content-Length:).*',header,re.IGNORECASE)
			sz = int(clength.group().strip())-len(post_head) if clength else False

		#get the size of the first chonk
		elif post_head!=b'':
			try:
				sz_end = post_head.index(b'\r')
				sz = post_head[:sz_end]
				post_head = post_head[sz_end:]
				sz = int(sz,base=16)+2
				firstround = True
			except ValueError:
				sz += post_head
				post_head = b''
			post_head = post_head[2:] if len(post_head)>2 else b''
		f.write(post_head)
		#print(header,sz)
		#print(header)
		#actually reading the file
		while True: 
			sz = b'' if chonkytime and not firstround else sz
			firstround = False #because it's not the first round anymore
			if chonkytime:
				if type(sz)!=int:
					while True:
						try:
							chonk = soc.recv(1)
						except:
							soc = reconnect(soc,hostnm,port,globalcookie)
							cookie = ''
							looprest = True
							break
						sz += chonk
						if sz[-1:] == b'\n':
							sz = int(sz[:-2],base=16)+2
							break
				elif post_head!=b'': #account for that posthead size
					sz -= len(post_head)
					post_head = b''
			if looprest:
				break
			if chonkytime and sz<=2:
				break
			pos = 0
			if sz==b'': #non chonkytime and no size available
				post_head_complete = not re.search(rb'\r\n\r\n',post_head)
				megachonk = b''
				while post_head_complete:
					chonk = b''
					try:	
						chonk = soc.recv(2048)
					except:
						soc = reconnect(soc,hostnm,port,globalcookie)
						cookie = ''
						looprest = True
					megachonk += chonk
					#print(megachonk)
					if looprest or not chonk.strip() or not megachonk or re.search(rb'\r\n\r\n',megachonk):
						break
				f.write(megachonk)
				if looprest:
					break
			while sz and pos<sz:
				chonk = soc.recv(min(2048,sz-pos))
				pos+=len(chonk)
				f.write(chonk) 

			if not chonkytime:
				break

			#remove the extra \r\n from the end of the chunk
			f.seek(-2,1)
			f.truncate()
			
			#if you'd like to see what's being parsed (per chonk for chonkytime or the entire file otherwise), uncomment this
			"""f.seek(-pos+2,1) #must account for removing \r\n from the end
			print(f.read()) 
			print(sz)"""

		#header things
		statuscode = re.search(r'(?<=HTTP/1\.1 )[0-9]+',header).group()
		#print(header)
		#is this an incorrect fucking filename? FUCK
		if statuscode == '404':
			print("FUCK YOU ",links[-1])
			f.close()
			del files[links[-1]]
			fin = links.pop()
			if globalfinished != None:
				globalfinished.append(fin)
			else:
				finishedlinks.append(fin)
			looprest = True
		#did they fucking MOVE IT OH MY GOD
		if statuscode=='301' or statuscode=='302':
			newloc = re.search(r'(?<=Location:).*',header).group().strip()
			f.close()
			del files[links[-1]]
			fin = links.pop()
			if globalfinished != None:
				globalfinished.append(fin)
			else:
				finishedlinks.append(fin)
			links.append(newloc)
			looprest = True
		#am i retarded yeah probably
		if statuscode == '400':
			raise Exception('malformed command: {}'.format(cmd))
		#are they shutting the door on me? ITS TIME TO FUCKING DIE
		if re.search(r'Connection: close',header,re.IGNORECASE):
			soc = reconnect(soc,hostnm,port,globalcookie)
			cookie = ''
			#print(header)
			looprest = True
		#im being rate limited aIYA
		if statuscode == '402':
			print("HEH")
			f.close()
			del files[links[-1]]
			#time.sleep(backoff)
			cookie = ''
			if globalcookie:
				with globalcookie.get_lock():
					globalcookie.value = b''
			looprest = True

		if looprest:
			if not links and linkqueue!=None:
				upcoming = linkfromglobal(linkqueue,globalfinished,lock)
				if not upcoming:
					break
				links.append(upcoming)	
			continue

		#take link off queue and prepare f to read
		fin = links.pop()
		if globalfinished != None:
			globalfinished.append(fin)
		else:
			finishedlinks.append(fin)
		f.seek(0)

		#cookie
		if not cookie:
			has_cookie = re.search(r'(?<=Cookie:)[^;]*',header)
			if has_cookie:
				if globalcookie:
					with globalcookie.get_lock():
						globalcookie.value = has_cookie.group().strip().encode()
				else:
					cookie = has_cookie.group().strip()

		#parsing links
		content_type = re.search(r'(?<=Content-Type:).*',header,re.IGNORECASE)
		if content_type and content_type.group().strip().lower() == 'text/html':
			try:
				txt = f.read().decode()
			except UnicodeDecodeError:
				txt = ''
			addl_links = list(filter(del_crap,re.findall(r'(?<=href=[\'\"])[^\'\"]*(?=[\'\"])', txt,re.IGNORECASE))) #read for href
			for item in filter(del_crap,re.findall(r'(?<=src=[\'\"])[^\'\"]*(?=[\'\"])', txt,re.IGNORECASE)): #read for src
				if item not in addl_links:
					addl_links.append(item)
			for item in filter(del_crap,re.findall(r'https*://\S*',txt,re.IGNORECASE)): #i dunno, maybe other buggers living about
				if item not in addl_links:
					addl_links.append(item)
			addl_links = map(lambda x:x[1:] if x[0:2] == './' else ('/'+x if x[0]!='/' else x), addl_links) #shave off './', or add '/'
			addl_links = map(lambda x:dirnm+x if x[:3]!='/..' else (x[3:] if '/' not in dirnm\
				else '/'.join(dirnm.split('/')[:-1])+x[3:]), addl_links) #add directory, backtrack directory if it's '../'
			if linkqueue!=None:
				for link in addl_links:
					linkqueue.append(link)
				upcoming = linkfromglobal(linkqueue,globalfinished,lock)
				if not upcoming:
					break
				links.append(upcoming)		
			else:
				for link in addl_links:
					if link not in finishedlinks:
						links.append(link)
			f.seek(0)
		elif linkqueue!=None:
			upcoming = linkfromglobal(linkqueue,globalfinished,lock)
			if not upcoming:
				break
			links.append(upcoming)	
		#Grace is tired
		#Take her home
		#break
		#What the fuck is up Richard

	if lock != None:
		lock.acquire()
	for file in files.keys():
		filenm = file.split('/')[-1] if '/' in file else file
		if filenm=='':
			#continue
			filenm = 'index.html'
		#handle duplicate files
		dup = 1
		filenm1 = filenm
		curdir = set(os.listdir(direc))
		while filenm1 in curdir:
			if '.' in filenm:
				name_end = filenm.index('.')
				filenm1 = filenm[:name_end]+'-'+str(dup)+filenm[name_end:]
			else:
				filenm1 += '-'+str(dup)
			dup+=1
		#write to an actual file
		with open(direc+('/' if direc[-1]!='/' else '')+filenm1,'wb') as f:
			f.write(files[file].read())
		files[file].close()
	if lock != None:
		lock.release()
	return 0

def multithread(hostnm,port,direc,processes,cookielock):
	globalcookie = mp.Array(ctypes.c_char,512) if cookielock else None
	locc = mp.Lock()
	kidager = mp.Manager()
	gf = kidager.list()
	lq = kidager.list(['/index.html'])
	ps = [mp.Process(target=webcrawl, args=(hostnm,port,direc),\
		kwargs={'globalcookie':globalcookie,'linkqueue':lq,'lock':locc,'globalfinished':gf,'pid':i+1}) for i in range(processes)]
	for p in ps:
		p.start()
	for p in ps:
		p.join()
	return 0

if __name__ == '__main__':
	parser = argparse.ArgumentParser(prog='mcrawl',add_help=False)
	parser.add_argument('-n','--max-flows',type=int,dest='nthreads',required=True)
	parser.add_argument('-h','--hostname',dest='hostnm',required=True)
	parser.add_argument('-p','--port',type=int,dest='port',required=True)
	parser.add_argument('-f','--local-directory',dest='dir',required=True)
	parser.add_argument('-cl','--cookie-lock',type=int,dest='cl',default=1)
	args = vars(parser.parse_args())
	print(multithread(args['hostnm'],args['port'],args['dir'],args['nthreads'],args['cl']) if args['nthreads']>1\
		else webcrawl(args['hostnm'],args['port'],args['dir']))

		
