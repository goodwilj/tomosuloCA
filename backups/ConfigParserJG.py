import os
import re
import numpy as np

def readconfig(fileName,ARFint,ARFfloat,Memory):
	config = {'numRS':{},'cycInEx':{},'cycInMem':{},'numFUs':{},'ROBentries':0,'CDBBuffEntries':0}
	commands = ["ld","sd","beq","bne","add","add.d","addi","sub","sub.d","mult.d"]
	commentVal = '"' ## Comment key

	with open(fileName,"r") as f:
		lines = f.read().splitlines()
	
	for i, line in enumerate(lines):
		###  lines 1-4 define the num of RS, Cycles in Ex, cycles in mem, and num of FUs 
		if i>0 and i<5:
			line = re.split(r'\t+',line)
			config['numRS'][line[0]]=line[1]
			config['cycInEx'][line[0]] = line[2]
			config['cycInMem'][line[0]] = line[3]
			config['numFUs'][line[0]] = line[4]

		###  lines 6 and 7 define number of ROB and CDB Buff Entries
		elif i==6:
			line = re.split(r'\t+',line)
			config['ROBentries'] = line[1]
		elif i ==7:
			line = re.split(r'\t+',line)
			config['CDBBuffEntries'] = line[1]

		### line 8 defines the initial registers
		elif i==8:
			line = re.split(', ',line)
			for reg in line:
				reg = reg.split("=")
				val = reg[1]
				rname = re.split('(\d+)',reg[0])
				rtype = rname[0]
				raddress = int(rname[1])
				if rname[0]=='R':
					ARFint[raddress]=val
				elif rname[0]=='F':
					ARFfloat[raddress]=val

		### line 9 defines the initial memory config
		elif i==9:
			line = re.split(', ',line)
			for mem in line:
				mem = mem.split('=')
				val = mem[1]
				mname = re.findall('\d+',mem[0])
				maddress = int(mname[0])
				Memory[maddress]=val
		### lines beyond 11 are instructions
		elif i>=11:
			inst = line.split(" ")
        	### Command is first val, case insensitive ###
			cmd = inst[0].lower() 

        	### if Command is comment, just move to next one ###
			if cmd == commentVal:
				continue

			if cmd not in commands:
				print("ERROR: Unknown instruction exiting")
				exit()

			data = inst[1:]

        	## ld: load a single precision floating point value to Fa
        	## sd: Store a single precision floating point value to memor
			if cmd in ["ld","sd"]:
				Fa = data[0].replace(",","")
            	### Need to parse the offset properly and remove ending )
				loc = data[1].replace(")","").split("(")
				offset = loc[0].replace(",","")
				reg = loc[1].replace(",","")
				print(cmd,Fa,offset,reg)
        
        	## beq: if Rs==Rt, branch to PC+4+offset << 2
        	## bne: if Rs!=Rt, branch to PC+4+offset << 2
			elif cmd in ["beq","bne"]:
				Rs = data[0].replace(",","")
				Rt = data[1].replace(",","")
				offset = data[2].replace(",","")
				print(cmd,Rs,Rt,offset)

        	##d = s <operation> t
			else:
				d = data[0].replace(",","")
				s = data[1].replace(",","")
				t = data[2].replace(",","")
				print(cmd,d,s,t)

	return config,ARFint,ARFfloat, Memory


if __name__ == "__main__":
	### init data structures

	#Architecture register files
	ARFint = np.zeros(32,dtype=np.int32)
	ARFfloat = np.zeros(32,dtype=np.float32)

	#Memory
	Memory = np.zeros(64)
	
	#ParseInputFile
	config,ARFint,ARFfloat,Memory = readconfig('config.txt',ARFint,ARFfloat,Memory)

	print(config['numRS'])
	print(config['cycInEx'])
	print(config['cycInMem'])
	print(config['numFUs'])
	print(config['ROBentries'])
	print(config['CDBBuffEntries'])
	print("ARFint")
	print(ARFint)
	print("ARFFloat")
	print(ARFfloat)
	print("Memory")
	print(Memory)


