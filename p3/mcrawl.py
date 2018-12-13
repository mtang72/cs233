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

def webcrawl(hostnm,port,direc,globalcookie=None,linkqueue=None,lock=None):
	soc = socket.socket()
	#soc.settimeout(5)
	try:
		soc.connect((hostnm,port))
	except:
		raise Exception("FUCK")
	links = [linkqueue.pop() if linkqueue!=None else '/index.html']
	backoff = 1
	cookie = ''
	sz = b''
	files = {}
	while links!=[]:
		cookie = globalcookie.value.decode() if globalcookie else cookie
		print(linkqueue, links)
		looprest = False #better way to reset loop

		#file handling
		if links[-1] in files:
			links.pop()
			links.append(linkqueue.pop())
			continue
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
		print(header,sz)
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
			links.pop()
			looprest = True
		#did they fucking MOVE IT OH MY GOD
		if statuscode=='301' or statuscode=='302':
			newloc = re.search(r'(?<=Location:).*',header).group().strip()
			f.close()
			del files[links[-1]]
			links.pop()
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
			if not links:
				links.append(linkqueue.pop())
			continue

		#take link off queue and prepare f to read
		links.pop()
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
		del_crap = lambda x:x and '#' not in x and not (('http://' in x or 'https://' in x)\
			and re.search(r'(?<=://)[^/]*',x).group()!=hostnm)
		try:
			txt = f.read().decode()
		except UnicodeDecodeError:
			txt = ''
		addl_links = list(filter(del_crap,re.findall(r'(?<=href=[\'\"])[^\'\"]*(?=[\'\"])', txt,re.IGNORECASE))) #read for href
		addl_links.extend(filter(del_crap,re.findall(r'(?<=src=[\'\"])[^\'\"]*(?=[\'\"])', txt,re.IGNORECASE))) #read for src
		addl_links = map(lambda x:x[1:] if x[0:2] == './' else ('/'+x if x[0]!='/' else x), addl_links) #shave off './', or add '/'
		addl_links = map(lambda x:dirnm+x if x[:3]!='/..' else x[3:], addl_links) #add directory, or not if it's '../'
		if linkqueue!=None:
			for link in addl_links:
				linkqueue.append(link)
			print(linkqueue)
			links.append(linkqueue.pop())
		else:
			links.extend(addl_links)
		f.seek(0)
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
	lq = mp.Manager().list(['/index.html'])
	ps = [mp.Process(target=webcrawl, args=(hostnm,port,direc),\
		kwargs={'globalcookie':globalcookie,'linkqueue':lq,'lock':locc}) for i in range(processes)]
	ps[0].start()
	ps[0].join()
	"""for p in ps:
		p.start()
	for p in ps:
		p.join()"""
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

		
