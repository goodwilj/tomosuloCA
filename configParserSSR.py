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
        print(config)

    config['ROBentries'] = lines[6].split()[1]
    config['CDBBuffEntries'] = lines[7].split()[1]

    Rvals = lines[8].split()
    print(Rvals)
    print(re.split('(\d+)',Rvals[0]))


if __name__ == '__main__':
    fileName = "config.txt"
    configParser(fileName)
    
