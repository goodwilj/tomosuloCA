import inputparser as ip

config,ARFint,ARFfloat,Memory,instructions = ip.configParser('config.txt')
instrBuffer = ip.instParser(instructions)

#Init ROB
ROB = [{'Type': '', 'Dst': '', 'Value': None, 'Fin': False} for i in range(int(config['ROBentries']))]
ROBptr = 0

#Init RAT and number of functional units (config[..][3] indicates input FU #)
RATint = {'R'+str(i) : 'R'+str(i)  for i in range(32)}
RATfloat = {'F'+str(i) : 'F'+str(i)  for i in range(32)}
FuncU = {'Integer': config['intadd'][3], 'FP Add': config['fpadd'][3],
         'FP Mult': config['fpmult'][3],'LD/SD': config['l/sunit'][3]}

#Init Reservation Stations
IntAddRs = [{'Op': '', 'Dst': '', 'Tag1':'','Tag2':'','Val1':None,'Val2':None} for i in range(config['intadd'][0])]
FPAddRs = [{'Op': '', 'Dst': '', 'Tag1':'','Tag2':'','Val1':None,'Val2':None} for i in range(config['fpadd'][0])]
FPMultRes = [{'Op': '', 'Dst': '', 'Tag1':'','Tag2':'','Val1':None,'Val2':None} for i in range(config['fpmult'][0])]
LSRes = [{'Op': '', 'Dst': '', 'Tag1':'','Tag2':'','Val1':None,'Val2':None} for i in range(config['l/sunit'][0])]


def issue(instr):
    switch(instr['Type']):
        case 'LD':
            if ROBptr < len(ROB-1) and LSRes:
                
            
        

nextInstr = instrBuffer[0]
#while (nextInstr != ''):
    #issue(nextInstr)

    #Execute
    

