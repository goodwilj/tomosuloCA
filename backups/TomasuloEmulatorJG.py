import inputparser as ip
import re

config,ARFint,ARFfloat,Memory,instructions = ip.configParser('config.txt') ## Get instructions and config
## Parse instructions ##
instrBuffer = ip.instParser(instructions)
instrBuffer.append(None);

## For each instruction, (iss,exec,mem,wb,c) ##
#timingTable = [(None,None,None,None,None)] * len(instructions)
timingTable = []

#Init ROB
ROB = [{'Type': '', 'Dst': '', 'Value': None, 'Fin': False} for i in range(int(config['ROBentries']))]
ROBhead = 0
ROBtail = 0
#Init RAT and number of functional units (config[..][3] indicates input FU #)
RATint = {'R'+str(i) : 'R'+str(i)  for i in range(32)}
RATfloat = {'F'+str(i) : 'F'+str(i)  for i in range(32)}

#Init Reservation Stations
#IntAddRs = [{'Op': '', 'Dst': '', 'Tag1':'','Tag2':'','Val1':None,'Val2':None} for i in range(config['intadd'][0])]
IntAddRs = []
#FPAddRs = [{'Op': '', 'Dst': '', 'Tag1':'','Tag2':'','Val1':None,'Val2':None} for i in range(config['fpadd'][0])]
FPAddRs = []
#FPMultRes = [{'Op': '', 'Dst': '', 'Tag1':'','Tag2':'','Val1':None,'Val2':None} for i in range(config['fpmult'][0])]
FPMultRes = []
#LSRes = [{'Op': '', 'Dst': '', 'Tag1':'','Tag2':'','Val1':None,'Val2':None} for i in range(config['l/sunit'][0])]
LSRes = []

def main():
    pc = 0 ## Program counter
    instNum = 0 ##instruction number
    cc = 1 ## Clock cycle


    ## Number of functional units for each ##
    FuncU = {'Integer': config['intadd'][3], 'FP Add': config['fpadd'][3], \
             'FP Mult': config['fpmult'][3],'LD/SD': config['l/sunit'][3]}
    

    
    firstInst = instrBuffer[pc]
    issued = issue(firstInst,pc)
    timingTable.append({'InstNum':instNum,'Type':firstInst['Type'],'iss':cc,'exec':None,'mem':None,'wb':None,'c':None})
    instNum = instNum+1
    pc = pc+1
    nextInst = instrBuffer[pc]
    while timingTable[instNum-1]['c']==None:
    #while nextInst:
        cc += 1
        ##process previous instructions
        ## commit
        execute(cc)
        if(nextInst!=None):
            issued = issue(nextInst,instNum)
            if issued:
                timingTable.append({'InstNum':instNum,'Type':nextInst['Type'],'iss':cc,'exec':None,'mem':None,'wb':None,'c':None})
                instNum = instNum+1
                pc = pc+1
                nextInst = instrBuffer[pc]
                print(timingTable)
            else:
                pass



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
    else:
        return
    
def writeback():
    pass

def memory():
    pass

def execute(cc):
    global timingTable
    
    if timingTable ==None:
        return
    else:
        for i, entry in enumerate(timingTable):
            if entry['exec']==None and entry['iss']!=None:
                t = entry['Type']
                if t in ["add","addi","sub","beq", "bne"]:
                    ##is there an integer add unit open?
                    
                    
                    for rs in IntAddRs:
                        if rs['instNum']==i:
                            if rs['Val1']!=None and rs['Val2']!=None:
                                timingTable[i]['exec']=cc
                elif t in ["add.d","sub.d"]:
                    pass
                elif t in ["ld","sd"]:
                    pass
            

def issue(inst,instNum):
    global ROB, ROBtail, RATint, RATfloat, ARFint, ARFfloats
    if ROBtail-ROBhead<int(config['ROBentries']):
        t = inst['Type']

        if t in ["add","addi","sub","bne", "beq"] and len(IntAddRs)<config['intadd'][0]:

            if t in ["add","addi","sub"]:
                #Read RAT and dispatch in Reservation station
                rs = RATint[inst['Rs']]
                rt = RATint[inst['Rt']]
                rsName = re.split('(\d+)',RATint[inst['Rs']])
                rtName = re.split('(\d+)',RATint[inst['Rt']])

                rsnum = int(rsName[1])
                rtnum = int(rtName[1])
                
                print(rsName)
                print(rtName)

                ##both dependent on instructions
                if rsName[0]=="ROB" and rtName[0]=="ROB":
                    
                    if ROB[rsnum]['Value']==None and ROB[rtnum]['Value']==None:
                        IntAddRs.append({'instNum': instNum,'Op': t, 'Dst': inst['Rd'], 'Tag1': rs,'Tag2': rt,'Val1':None,'Val2':None})
                    elif ROB[rsnum]['Value']!=None and ROB[rtnum]['Value']==None:
                        IntAddRs.append({'instNum': instNum,'Op': t, 'Dst': inst['Rd'], 'Tag1': '','Tag2': rt,'Val1':ROB[rsnum]['Value'],'Val2':None})
                    elif ROB[rsnum]['Value']==None and ROB[rtnum]['Value']!=None:
                        IntAddRs.append({'instNum': instNum,'Op': t, 'Dst': inst['Rd'], 'Tag1': rs,'Tag2': rt,'Val1':None,'Val2':ROB[rtnum]['Value']})
                    else:
                        IntAddRs.append({'instNum':instNum,'Op': t, 'Dst': inst['Rd'], 'Tag1': '','Tag2': '','Val1':ROB[rsnum]['Value'],'Val2':ROB[rtnum]['Value']})

                #Only source with ROB
                elif rsName[0]=="ROB":
                    if ROB[rsnum]['Value']==None:
                        IntAddRs.append({'instNum':instNum,'Op': t, 'Dst': inst['Rd'], 'Tag1': rs,'Tag2': '','Val1':None,'Val2':ARFint[rtnum]})
                    else:
                        IntAddRs.append({'instNum':instNum,'Op': t, 'Dst': inst['Rd'], 'Tag1': '','Tag2': '','Val1':ROB[rsnum]['Value'],'Val2':ARFint[rtnum]})

                #only target with ROB
                elif rtName[0]=="ROB":

                    if ROB[rtnum]['Value']==None:
                        IntAddRs.append({'instNum':instNum,'Op': t, 'Dst': inst['Rd'], 'Tag1': '','Tag2': rt,'Val1':ARFint[rsnum],'Val2':None})
                    else:
                        IntAddRs.append({'instNum':instNum,'Op': t, 'Dst': inst['Rd'], 'Tag1': '','Tag2': '','Val1':ARFint[rsnum],'Val2':ROB[rtnum]['Value']})

                #both sources not in ROB
                else:
                    IntAddRs.append({'instNum':instNum,'Op': t, 'Dst': inst['Rd'], 'Tag1': '','Tag2': '','Val1':ARFint[rsnum],'Val2':ARFint[rtnum]})
                        
                #{'Op': '', 'Dst': '', 'Tag1':'','Tag2':'','Val1':None,'Val2':None}
                ROB[ROBtail]= {'Type': t, 'Dst': inst['Rd'], 'Value': None, 'Fin': False}
                ROBtail+=1

            ##branch instruction
            else:
                
                ROB[ROBtail]= {'Type': t, 'Dst': '', 'Value': None, 'Fin': False}
            return 1

        elif t in ["add.d","sub.d"] and len(FPAddRs)<config['fpadd'][0]:

            #Read RAT and dispatch in Reservation station
            rs = RATfloat[inst['Rs']]
            rt = RATfloat[inst['Rt']]
            rsName = re.split('(\d+)',RATfloat[inst['Rs']])
            rtName = re.split('(\d+)',RATfloat[inst['Rt']])

            rsnum = int(rsName[1])
            rtnum = int(rtName[1])
                
            print(rsName)
            print(rtName)

            ##both dependent on instructions
            if rsName[0]=="ROB" and rtName[0]=="ROB":
                    
                if ROB[rsnum]['Value']==None and ROB[rtnum]['Value']==None:
                    FPAddRs.append({'instNum':instNum,'Op': t, 'Dst': inst['Rd'], 'Tag1': rs,'Tag2': rt,'Val1':None,'Val2':None})
                elif ROB[rsnum]['Value']!=None and ROB[rtnum]['Value']==None:
                    FPAddRs.append({'instNum':instNum,'Op': t, 'Dst': inst['Rd'], 'Tag1': '','Tag2': rt,'Val1':ROB[rsnum]['Value'],'Val2':None})
                elif ROB[rsnum]['Value']==None and ROB[rtnum]['Value']!=None:
                    FPAddRs.append({'instNum':instNum,'Op': t, 'Dst': inst['Rd'], 'Tag1': rs,'Tag2': rt,'Val1':None,'Val2':ROB[rtnum]['Value']})
                else:
                    FPAddRs.append({'instNum':instNum,'Op': t, 'Dst': inst['Rd'], 'Tag1': '','Tag2': '','Val1':ROB[rsnum]['Value'],'Val2':ROB[rtnum]['Value']})

            #Only source with ROB
            elif rsName[0]=="ROB":
                if ROB[rsnum]['Value']==None:
                    FPAddRs.append({'instNum':instNum,'Op': t, 'Dst': inst['Rd'], 'Tag1': rs,'Tag2': '','Val1':None,'Val2':ARFfloat[rtnum]})
                else:
                    FPAddRs.append({'instNum':instNum,'Op': t, 'Dst': inst['Rd'], 'Tag1': '','Tag2': '','Val1':ROB[rsnum]['Value'],'Val2':ARFfloat[rtnum]})

            #only target with ROB
            elif rtName[0]=="ROB":

                if ROB[rtnum]['Value']==None:
                    FPAddRs.append({'instNum':instNum,'Op': t, 'Dst': inst['Rd'], 'Tag1': '','Tag2': rt,'Val1':ARFfloat[rsnum],'Val2':None})
                else:
                    FPAddRs.append({'instNum':instNum,'Op': t, 'Dst': inst['Rd'], 'Tag1': '','Tag2': '','Val1':ARFfloat[rsnum],'Val2':ROB[rtnum]['Value']})

            #both sources not in ROB
            else:
                FPAddRs.append({'instNum':instNum,'Op': t, 'Dst': inst['Rd'], 'Tag1': '','Tag2': '','Val1':ARFfloat[rsnum],'Val2':ARFfloat[rtnum]})
            
            ROB[ROBtail]= {'Type': t, 'Dst': inst['Rd'], 'Value': None, 'Fin': False}
            
            return 1

        elif t in ['mult.d'] and len(FPMultRes)<config[fpmult][0]:
            ROB[ROBtail]= {'Type': t, 'Dst': inst['Rd'], 'Value': None, 'Fin': False}
            return 1

        elif t in ['ld','sd'] and len(LSRes)<config['l/sunit'][0]:
            ROB[ROBtail]= {'Type': t, 'Dst': '', 'Value': None, 'Fin': False}
            return 1
    else:
        return 0
        

 
                
if __name__ == '__main__':
    main()
