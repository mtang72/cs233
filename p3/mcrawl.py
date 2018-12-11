#!/usr/bin/env python3
import argparse, socket, multiprocessing, re, os, tempfile

def webcrawl(hostnm,port,files):
	soc = socket.socket()
	try:
		soc.connect((hostnm,port))
	except:
		raise Exception("FUCK")
	links = ['/index.html']
	while links!=[]:

		#get header
		cmd = 'HEAD {} HTTP/1.1\r\nHost: {}\r\n\r\n'.format(links[-1],hostnm)
		try:
			soc.sendall(cmd.encode())
		except:
			raise Exception('fuck')
		header = ''
		while True:
			rec = soc.recv(2048)
			header += rec.decode()
			if rec[-4:] == b'\r\n\r\n':
				break
		
		#is this an incorrect fucking filename? FUCK
		if '404' in header.split('\n')[0]:
			print("FUCK YOU ",links[-1])
			links.pop()
			continue

		#did they fucking MOVE IT OH MY GOD
		if '301' in header.split('\n')[0]:
			newloc = re.search(r'(?<=Location:).*',header).group().strip()
			links.pop()
			links.append(newloc)
			continue

		#are they rate limiting me? ITS TIME TO FUCKING DIE
		#if 

		#obviously, to determine if it's chonkytime or not
		encoding_type = re.search(r'(?<=Transfer-Encoding:).*',header,re.IGNORECASE)
		chonkytime = encoding_type!=None and re.match(r'chunked',encoding_type.group().strip(),re.IGNORECASE)!=None

		#now get
		cmd = 'GET'+cmd[4:]
		try:
			soc.sendall(cmd.encode())
		except:
			raise Exception('fuck')

		#skip header to start read
		pos = 0
		while pos<len(header):
			rec = soc.recv(len(header))
			pos += len(rec)

		#open file to write in and dir to attach to given links
		filenm, dirnm = '',''
		if '/' in links[-1]:
			filenm = links[-1].split('/')[-1]
			dirnm = '/'.join(links[-1].split('/')[:-1])
		else:
			filenm = links[-1].split('/')[-1] if '/' in links[-1] else links[-1]

		#handle duplicate files
		dup = 1
		filenm1 = filenm
		curdir = set(os.listdir())
		while filenm1 in curdir:
			if '.' in filenm:
				name_end = filenm.index('.')
				filenm1 = filenm[:name_end]+'-'+str(dup)+filenm[name_end:]
			else:
				filenm1 += '-'+str(dup)
			dup+=1
		filenm = filenm1
		files[filenm] = tempfile.TemporaryFile()
		f = files[filenm]

		if not chonkytime:
			sz = int(re.search(r'(?<=Content-Length:).*',header,re.IGNORECASE).group().strip())

		#actually reading the file
		while True: 
			sz = '' if chonkytime else sz
			while chonkytime:
				chonk = soc.recv(1)
				if chonk == b'\n':
					sz = int(sz[:-1],base=16)+2
					break
				sz += chonk.decode()
			if chonkytime and sz==2:
				break
			pos = 0
			while pos<sz:
				chonk = soc.recv(min(2048,sz-pos))
				pos+=len(chonk)
				f.write(chonk if chonk[-2:]!='\r\n' else chonk[:-2]) #remove the extra \r\n from the end of the chunk
			
			#if you'd like to see what's being parsed (per chonk for chonkytime or the entire file otherwise), uncomment this
			"""f.seek(-pos+2,1) #must account for removing \r\n from the end
			print(f.read()) 
			print(sz)"""

			if not chonkytime:
				break
		links.pop()
		f.seek(0)

		#parsing links
		del_crap = lambda x:x.strip()!='' and '#' not in x\
			and not (('http://' in x or 'https://' in x) and re.search(r'(?<=://)[^/]*',x).group()!=hostnm)
		try:
			txt = f.read().decode()
		except UnicodeDecodeError:
			txt = ''
		addl_links = list(filter(del_crap,re.findall(r'(?<=href=[\'\"])[^\'\"]*(?=[\'\"])', txt)))
		addl_links.extend(filter(del_crap,re.findall(r'(?<=src=[\'\"])[^\'\"]*(?=[\'\"])', txt)))
		addl_links = map(lambda x:x[1:] if x[0:2] == './' else ('/'+x if x[0]!='/' else x), addl_links)
		addl_links = map(lambda x:dirnm+x, addl_links)
		links.extend(addl_links)
		print(links)
		f.seek(0)
		#Grace is tired
		#Take her home
		#break
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
	files = {}
	webcrawl(args['hostnm'],args['port'],files)
	for file in files.keys():
		with open(file,'wb') as f:
			f.write(files[file].read())
		files[file].close()
