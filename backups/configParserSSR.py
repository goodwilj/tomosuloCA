import os
import re
import numpy as np

def configParser(fileName):
    ### Initialize stuff ###
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

    config['ROBentries'] = lines[6].split()[1]
    config['CDBBuffEntries'] = lines[7].split()[1]

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
    print(instructions)

    return (config,ARFint,ARFfloat,Memory,instructions)

if __name__ == '__main__':
    fileName = "config.txt"
    configParser(fileName)
    
