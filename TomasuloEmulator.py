import inputparser as ip


#Init ROB
global ROB = [{'Type': '', 'Dst': '', 'Value': None, 'Fin': False} for i in range(int(config['ROBentries']))]
global ROBhead = 0
global ROBtail = 0
#Init RAT and number of functional units (config[..][3] indicates input FU #)
global RATint = {'R'+str(i) : 'R'+str(i)  for i in range(32)}
global RATfloat = {'F'+str(i) : 'F'+str(i)  for i in range(32)}

def main():
    pc = 0 ## Program counter
    cc = 0 ## Clock cycle
    config,ARFint,ARFfloat,Memory,instructions = ip.configParser('config.txt') ## Get instructions and config
    global config = config

    ## For each instruction, (iss,exec,mem,wb,c) ##
    #timingTable = [(None,None,None,None,None)] * len(instructions)
    timingTable = [{}]

    ## Parse instructions ##
    instrBuffer = ip.instParser(instructions)

    ## Number of functional units for each ##
    FuncU = {'Integer': config['intadd'][3], 'FP Add': config['fpadd'][3], \ 'FP Mult': config['fpmult'][3],'LD/SD': config['l/sunit'][3]}
    
    #Init Reservation Stations
    #IntAddRs = [{'Op': '', 'Dst': '', 'Tag1':'','Tag2':'','Val1':None,'Val2':None} for i in range(config['intadd'][0])]
    global IntAddRs = []
    #FPAddRs = [{'Op': '', 'Dst': '', 'Tag1':'','Tag2':'','Val1':None,'Val2':None} for i in range(config['fpadd'][0])]
    global FPAddRs = []
    #FPMultRes = [{'Op': '', 'Dst': '', 'Tag1':'','Tag2':'','Val1':None,'Val2':None} for i in range(config['fpmult'][0])]
    global FPMultRes = []
    #LSRes = [{'Op': '', 'Dst': '', 'Tag1':'','Tag2':'','Val1':None,'Val2':None} for i in range(config['l/sunit'][0])]
    global LSRes = []

    while nextInst:
        ## commit

        cc += 1

def commit():
    if ROB[ROBhead]['Fin']:
        t = ROB[ROBhead]['Type']
        Rd = ROB[ROBHead]['Dst']
        ## integers ##
        if t in ["add","addi","sub"]:
            ARFint[Rd] = ROB[ROBhead['Value']]

            ## You can only remove yourself ##
            if RATint[Rd] == 'R' + str(ROBhead):
                RATint[Rd] = Rd

        ## Floating point ##
        elif t in ["mult.d","add.d","ld"]:
            ARFfloat[Rd] = ROB[ROBhead['Value']]

            ## You can only remove yourself ##
            if RATfloat[Rd] == 'F' + str(ROBhead):
                RATfloat[Rd] = Rd

 
                
if __name__ == '__main__':
    main()
