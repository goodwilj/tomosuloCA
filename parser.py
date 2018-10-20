import os

""" Parse the assembly file and split instructions """
def fileParser(fileName):
    commands = ["ld","sd","beq","bne","add","add.d","addi","sub","sub.d","mult.d"]
    commentVal = '"' ## Comment key

    ### Read file in ###
    with open(fileName,"r") as f:
        lines = f.read().splitlines()
    splitLines = [l.split(" ") for l in lines]

    ### Loop through Instructions ###
    for i in range(len(splitLines)):
        inst = splitLines[i]
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
        ## sd: Store a single precision floating point value to memory
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
        

if __name__ == '__main__':
    fileParser('testAssembly.txt')
