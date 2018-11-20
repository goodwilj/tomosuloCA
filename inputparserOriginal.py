import os
import re
import numpy as np

"""
    Parse the header for the configurations
    @param fileName: input file containing configuration and instructions
"""
def configParser(fileName):
    ### Initialize structures ###
    ARFint = np.zeros(32,dtype=np.int32)
    ARFfloat = np.zeros(32,dtype=np.float32)
    Memory = np.zeros(64)

    with open(fileName,"r") as f:
        lines = f.read().splitlines() 
    ### Clean up tabs with spaces###
    lines = [re.sub("\t+"," ",l) for l in lines]
    config = {}

    ### Units ###
    for i in range(1,5):
        line = lines[i].split()
        ### if line is empty or a header, skip it ###
        if not line or i == 0:
            continue
        ### numRs CyclesInEx CyclesInMem numFUs ###
        config[line[0].lower()] = [int(j) for j in line[1:]]

    config['ROBentries'] = lines[6].split()[-1]
    config['CDBBuffEntries'] = lines[7].split()[-1]

    regs = lines[8].split()
    for reg in regs:
        splitReg = reg.replace(",","").split("=")
        regName = re.split('(\d+)',splitReg[0])
        ### [regType, regAddr, "=", regVal, ","] ###
        rtype = regName[0].lower()

        try:
            raddr = int(regName[1])
        except:
            print("Unknown Register Address",raddr,"\nExiting...")
            exit()

        rval = splitReg[1]
        try:
            if rtype == 'r':
                ARFint[raddr] = rval
            elif rtype == 'f':
                ARFfloat[raddr] = rval
            else:
                print("Unknown Register Type: ", rtype, "\nExiting...")
                exit()
        except:
            print("Unknown data type:",rval,"\nExiting")
            exit()

    memInit = lines[9].split()
    for mem in memInit:
        splitMem = mem.replace(",","").split("=")
        maddr = int(re.findall('\d+',splitMem[0])[0])
        mval = splitMem[1]
        Memory[maddr] = mval

    instructions = lines[10:]

    return (config,ARFint,ARFfloat,Memory,instructions)

""" 
    Parse the assembly file and split instructions
    @param instructions: List of lines containing instructions
"""
def instParser(instructions):
    commands = ["ld","sd","beq","bne","add","add.d","addi","sub","sub.d","mult.d"]
    commentVal = '"' ## Comment key

    instrList = []
    ### Loop through Instructions ###
    for i in range(len(instructions)):
        inst = instructions[i].split()
        ### Don't want empty lines ###
        if not inst:
            continue
        ### Command is first val, case insensitive ###
        print(inst)
        cmd = inst[0].lower() 

        ### if Command is comment, just move to next one ###
        if cmd == commentVal:
            continue

        if cmd not in commands:
            print("ERROR: Unknown instruction:",cmd,"\nExiting...")
            exit()

        data = inst[1:]
        
        ## ld: load a single precision floating point value to Fa
        ## sd: Store a single precision floating point value to memory
        if cmd in ["ld","sd"]:
            Fa = data[0].replace(",","")
            ### Need to parse the offset properly and remove ending )
            loc = data[1].replace(")","").split("(")
            offset = loc[0].replace(","," ").split()[0]
            reg = loc[1].replace(","," ").split()[0].upper()
            instrList.append({'Type': cmd,'Fa':Fa,'offset':offset,'Ra':reg})
            print(cmd,Fa,offset,reg)
        
        ## beq: if Rs==Rt, branch to PC+4+offset << 2
        ## bne: if Rs!=Rt, branch to PC+4+offset << 2
        elif cmd in ["beq","bne"]:
            Rs = data[0].replace(","," ").split()[0].upper()
            Rt = data[1].replace(","," ").split()[0].upper()
            offset = data[2].replace(","," ").split()[0]
            instrList.append({'Type': cmd,'Rs':Rs,'offset':offset,'Rt':Rt})
            print(cmd,Rs,Rt,offset)

        ##d = s <operation> t
        else:
            d = data[0].replace(","," ").split()[0].upper()
            s = data[1].replace(","," ").split()[0].upper()
            t = data[2].replace(","," ").split()[0].upper()
            instrList.append({'Type': cmd,'Rd':d,'Rs':s,'Rt':t})
            print(cmd,d,s,t)

    return (instrList)
        

if __name__ == '__main__':
    config,ARFint,ARFfloat,Memory,instructions = configParser('config.txt')
    instrList = instParser(instructions)
