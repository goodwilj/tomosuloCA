import inputparser as ip
import re


config,ARFint,ARFfloat,Memory,instructions = ip.configParser('config.txt') ## Get instructions and config
## Parse instructions ##
instrBuffer = ip.instParser(instructions)
instrBuffer.append(None);
print(instrBuffer)

## For each instruction, (iss,exec,mem,wb,c) ##
#timingTable = [(None,None,None,None,None)] * len(instructions)
timingTable = []

#Init ROB
ROB = [{'instNum': None, 'Type': '', 'Dst': '', 'Value': None, 'Fin': False} for i in range(int(config['ROBentries']))]
ROBhead = 0
ROBtail = 0
#Init CDB
CDBbuffer = [{'instNum': None, 'Dst': '','Value': None,'FinalCycle': None,'Occupied': False} for i in range(int(config['CDBBuffEntries']))]
#Init RAT and number of functional units (config[..][3] indicates input FU #)
RATint = {'R'+str(i) : 'R'+str(i)  for i in range(32)}
RATfloat = {'F'+str(i) : 'F'+str(i)  for i in range(32)}

## Number of functional units for each ##
IntAddFU = [{'Type': '','instNum': None, 'Dst': '','Value': None,'FinalCycle': None,'Occupied': False} for i in range(config['intadd'][3])]
FPAddFU = [{'Type': '','instNum': None, 'Dst': '','Value': None,'FinalCycle': None,'Occupied': False} for i in range(config['fpadd'][3])]
FPMultFU = [{'Type': '','instNum': None, 'Dst': '','Value': None,'FinalCycle': None,'Occupied': False} for i in range(config['fpmult'][3])]
LSFU = [{'Type': '','instNum': None, 'Dst': '','Value': None,'FinalCycle': None,'Occupied': False} for i in range(config['l/sunit'][3])]

#Init Reservation Stations
#IntAddRs = [{'Op': '', 'Dst': '', 'Tag1':'','Tag2':'','Val1':None,'Val2':None} for i in range(config['intadd'][0])]
IntAddRs = []
#FPAddRs = [{'Op': '', 'Dst': '', 'Tag1':'','Tag2':'','Val1':None,'Val2':None} for i in range(config['fpadd'][0])]
FPAddRs = []
#FPMultRs = [{'Op': '', 'Dst': '', 'Tag1':'','Tag2':'','Val1':None,'Val2':None} for i in range(config['fpmult'][0])]
FPMultRs = []
#LSRes = [{'Op': '', 'Dst': '', 'Tag1':'','Tag2':'','Val1':None,'Val2':None} for i in range(config['l/sunit'][0])]
LSRs = []
MemOccupied=False
MemFinalCycle=0

pc = 0 ## Program counter

def main():
    global pc
    instNum = 0 ##instruction number
    cc = 1 ## Clock cycle
    firstInst = instrBuffer[pc]
    #print(type(firstInst['offset']))
    issued = issue(firstInst,pc)
    timingTable.append({'InstNum':instNum,'Type':firstInst['Type'],'Instruction':firstInst,'iss':cc,'exec':None,'mem':None,'wb':None,'c':None})
    instNum = instNum+1
    pc = pc+1
    nextInst = instrBuffer[pc]

    while timingTable[instNum-1]['c']==None:
    #while nextInst:
        cc += 1
        if cc == MemFinalCycle:
            MemOccupied = False
        ##process previous instructions
        commit(cc)
        writeback(cc)
        memory(cc)
        branchtaken = execute(cc)
        print(pc)
        if branchtaken:
            nextInst = instrBuffer[pc]
        ##print_timingTable()
        if(nextInst!=None):
            issued = issue(nextInst,instNum)
            if issued:
                timingTable.append({'InstNum':instNum,'Type':nextInst['Type'],'Instruction':nextInst,'iss':cc,'exec':None,'mem':None,'wb':None,'c':None})
                instNum = instNum+1
                if instrBuffer[pc+1] is not None:
                    pc = pc+1
                    nextInst = instrBuffer[pc]
                else:
                    nextInst = None

            else:
                pass
    print_timingTable()

    



def commit(cc):
    global ROBhead, RATint, ARFint, LSRs, Memory, MemOccupied, MemFinalCycle
    ##if an sd entry in the LSRs is finished, pop it out
    for ientry, rsentry in enumerate(LSRs):
        if rsentry['Op']=='sd' and rsentry['MemFinalCycle'] is not None and rsentry['MemFinalCycle']+1==cc:
            LSRs.pop(ientry)
            MemOccupied=False
        if rsentry['Op']=='ld' and rsentry['MemFinalCycle'] is not None and rsentry['MemFinalCycle']+1==cc:
            MemOccupied=False

    ##For branch instructions, simply update the ROB after execution
    for entry in IntAddFU:
        if entry['FinalCycle'] is not None and entry['FinalCycle']+1 == cc and entry['Type'] in ['beq','bne']:
            for ROBi, ROBentry in enumerate(ROB):
                if ROBentry['instNum']==entry['instNum']:
                    ROBentry['Value'] = entry['Value']
                    ROBentry['Fin']= True
                    entry['Occupied'] = False

    if ROB[ROBhead]['Fin']:
        t = ROB[ROBhead]['Type']
        Rd = ROB[ROBhead]['Dst']
        #print(ROBhead)
        #print(ROB[ROBhead])
        ## integers ##
        if t in ["add","addi","sub"]:
            Rdint = int(Rd[1:])
            ARFint[Rdint] = ROB[ROBhead]['Value']

            ## You can only remove yourself ##
            if RATint[Rd] == 'ROB' + str(ROBhead):
                RATint[Rd] = Rd

            timingTable[ROB[ROBhead]['instNum']]['c'] = cc
            ROBhead+=1

        ## Floating point ##
        elif t in ["mult.d","add.d","sub.d"]:
            Rdfloat = int(Rd[1:])
            ARFfloat[Rdfloat] = ROB[ROBhead]['Value']

            ## You can only remove yourself ##
            if RATfloat[Rd] == 'ROB' + str(ROBhead):
                RATfloat[Rd] = Rd

            timingTable[ROB[ROBhead]['instNum']]['c'] = cc
            ROBhead+=1
        elif t == "ld":
            Rdfloat = int(Rd[1:])
            ARFfloat[Rdfloat] = ROB[ROBhead]['Value']

            ## You can only remove yourself ##
            if RATfloat[Rd] == 'ROB' + str(ROBhead):
                RATfloat[Rd] = Rd

            timingTable[ROB[ROBhead]['instNum']]['c'] = cc
            ROBhead+=1
        elif t == "sd":
            ###IMPORTANT: if memory is not occupied
            if not MemOccupied:
                for ientry,rsentry in enumerate(LSRs):
                    if rsentry['Op'] == 'sd':
                        if ROB[ROBhead]['instNum']==rsentry['instNum'] and rsentry['FinalCycle'] is not None and  cc >= (rsentry['FinalCycle']+1):
                            address = rsentry['address']
                            Memory[address] = rsentry['Val1']
                            timingTable[ROB[ROBhead]['instNum']]['c'] = str(cc) + '-' + str(cc+config['l/sunit'][2])
                            ROBhead+=1
                            MemOccupied = True
                            MemFinalCycle = cc+config['l/sunit'][2]
                            rsentry['MemFinalCycle']=MemFinalCycle
        elif t in ['beq','bne']:
            timingTable[ROB[ROBhead]['instNum']]['c'] = cc
            ROBhead+=1
    else:
        return
    
def writeback(cc):
    global IntAddRs,FPAddRs,FPMultRs,LSRs
    global IntAddFU,FPAddFU,FPMultFU,LSFU
    CDBoccupied = False
    for entry in CDBbuffer:
        if entry['Occupied']:
            for ROBi, ROBentry in enumerate(ROB):
                if 'ROB'+str(ROBi) == entry['Dst']:
                    ROBentry['Value'] = entry['Value']
                    ROBentry['Fin']= True
            for rs in [IntAddRs,FPAddRs,FPMultRs,LSRs]:
                for RSentry in rs:
                    if RSentry['Tag1']==entry['Dst']:
                        RSentry['Val1']=entry['Value']
                        RSentry['Tag1']=''
                    if RSentry['Tag2']==entry['Dst']:
                        RSentry['Val2']=entry['Value']
                        #RSentry['Tag2']=''
            entry['Occupied'] = False
            timingTable[entry['instNum']]['wb'] = cc
            CDBoccupied = True
    for FU in [IntAddFU,FPAddFU,FPMultFU]:
        for entry in FU:
            ## For instructions (with exception of branch) that have finished in the functional unit, write them back or hold them in the CDBbuffer 
            if entry['FinalCycle'] is not None and entry['FinalCycle']+1 == cc and entry['Type'] not in ['beq','bne']:
                #print('Exec Done!')
                if not CDBoccupied:
                    for ROBi, ROBentry in enumerate(ROB):
                        if 'ROB'+str(ROBi) == entry['Dst']:
                            ROBentry['Value'] = entry['Value']
                            ROBentry['Fin']= True
                    for rs in [IntAddRs,FPAddRs,FPMultRs,LSRs]:
                        for RSentry in rs:
                            if RSentry['Tag1']==entry['Dst']:
                                RSentry['Val1']=entry['Value']
                                RSentry['Tag1']='replaced'
                            if RSentry['Tag2']==entry['Dst']:
                                RSentry['Val2']=entry['Value']
                                RSentry['Tag2']='replaced'
                    entry['Occupied'] = False
                    timingTable[entry['instNum']]['wb'] = cc
                    CDBoccupied = True
                else:
                    for CDBentry in CDBbuffer:
                        if not CDBentry['Occupied']:
                            CDBentry=entry
                            entry['Occupied'] = False


    ##for load/store writing the address back to the LSRs
    for ientry, entry in enumerate(LSRs):
        if entry['Op']=='ld':
            if entry['MemFinalCycle'] is not None and entry['MemFinalCycle']+1 == cc:
                    #write address back to RS
                    for ROBi, ROBentry in enumerate(ROB):
                        if ROBentry['instNum']==entry['instNum']:
                            ROBentry['Value'] = entry['Val1']
                            ROBentry['Fin']= True
                    for RSentry in LSRs:
                        if RSentry['instNum']==entry['instNum']:
                            RSentry['address']=entry['address']
                    #entry['Occupied'] = False
                    timingTable[entry['instNum']]['wb'] = cc
                    LSRs.pop(ientry)

    ##remove any store instructions from functional if they are done
    for fu in LSFU:
        if fu['FinalCycle'] is not None and fu['FinalCycle']+1==cc:
            fu['Occupied']=False
                            

def memory(cc):
    ##only for load instruction'
    global MemOccupied,MemFinalCycle
    for LSQentry in LSRs:
        if LSQentry['Op'] == 'ld' and LSQentry['address'] is not None and cc>=LSQentry['FinalCycle']+1:
            for LSQentry2 in reversed(LSRs):
                if LSQentry2['Op'] == 'sd' and LSQentry2['address'] == LSQentry['address']:
                    LSQentry['Val1'] = LSQentry2['Val1']
                    timingTable[LSQentry['instNum']]['mem'] = str(cc)
                    LSQentry['MemFinalCycle'] = cc
                    return
            if not MemOccupied:
                MemOccupied = True
                MemFinalCycle = cc+config['l/sunit'][2]
                LSQentry['MemFinalCycle'] = MemFinalCycle
                LSQentry['Val1'] = Memory[LSQentry['address']]
                timingTable[LSQentry['instNum']]['mem'] = str(cc) + '-' + str(cc+config['l/sunit'][2])
                return

    

def execute(cc):
    global timingTable, pc
    global IntAddRs, FPAddRs, FPMultRs, LSRs
    global IntAddFU, FPAddFU, FPMultFU, LSFU
    
    if timingTable is None:
        return False
    else:
        for i, entry in enumerate(timingTable):
            if entry['exec'] is None and entry['iss'] is not None:
                t = entry['Type']
                if t in ["add","addi","sub","beq", "bne"]:
                    IntAddRs, IntAddFU = pushInstToExec(cc,IntAddRs,IntAddFU,t,i,config['intadd'][1])                        
                elif t in ["add.d","sub.d"]:
                    FPAddRs, FPAddFU = pushInstToExec(cc,FPAddRs,FPAddFU,t,i,config['fpadd'][1])
                elif t in ["mult.d"]:
                    FPMultRs, FPMultFU = pushInstToExec(cc,FPMultRs,FPMultFU,t,i,config['fpmult'][1])
                elif t in ["ld","sd"]:
                    LSRs, LSFU = pushInstToExec(cc,LSRs,LSFU,t,i,config['l/sunit'][1])

        for entry in IntAddFU:
            if entry['FinalCycle'] is not None and entry['FinalCycle']+1 == cc and entry['Type'] in ['beq','bne']:
                if entry['Value']:
                    pc = (pc+entry['offset'])
                    print('here')
                    return True

        return False


def issue(inst,instNum):
    global ROB, ROBtail, RATint, RATfloat, ARFint, ARFfloat, IntAddRs, FPAddRs
    if ROBtail-ROBhead<int(config['ROBentries']):
        t = (inst['Type'])

        if t in ["add","addi","sub","beq", "bne"] and len(IntAddRs)<config['intadd'][0]:

            if t in ["add","addi","sub"]:
                IntAddRs, RATint = pushtoRS(t, inst, instNum, IntAddRs, RATint, ARFint)
                #{'Op': '', 'Dst': '', 'Tag1':'','Tag2':'','Val1':None,'Val2':None}
                ##update ROB
                ROB[ROBtail]= {'instNum': instNum,'Type': t, 'Dst': inst['Rd'], 'Value': None, 'Fin': False}
                ROBtail+=1

            ##branch instruction
            else:
                IntAddRs, RATint = pushtoRS(t, inst, instNum, IntAddRs, RATint, ARFint)
                ROB[ROBtail]= {'instNum': instNum,'Type': t, 'Dst': '', 'Value': None, 'Fin': False}
                ROBtail+=1
                

            return 1
        
        ## FP Add    
        elif t in ["add.d","sub.d"] and len(FPAddRs)<config['fpadd'][0]:
            FPAddRs, RATfloat = pushtoRS(t, inst, instNum, FPAddRs, RATfloat, ARFfloat)
            #{'Op': '', 'Dst': '', 'Tag1':'','Tag2':'','Val1':None,'Val2':None}
            ##update ROB
            ROB[ROBtail]= {'instNum': instNum,'Type': t, 'Dst': inst['Rd'], 'Value': None, 'Fin': False}
            ROBtail+=1
            
            return 1

        elif t in ['mult.d'] and len(FPMultRs)<config['fpmult'][0]:
            FPMultRs, RATfloat = pushtoRS(t, inst, instNum, FPMultRs, RATfloat, ARFfloat)
            #{'Op': '', 'Dst': '', 'Tag1':'','Tag2':'','Val1':None,'Val2':None}
            ##update ROB
            ROB[ROBtail]= {'instNum': instNum,'Type': t, 'Dst': inst['Rd'], 'Value': None, 'Fin': False}
            ROBtail+=1
            
            return 1
            
            
        elif t in ['ld','sd'] and len(LSRs)<config['l/sunit'][0]:
            Ra = RATint[inst['Ra']]
            raName = re.split('(\d+)',Ra)
            ranum = int(raName[1])
            offset = int(inst['offset'])

            
            if t == 'ld':
                renameddest = 'ROB'+str(ROBtail)
                
                if raName[0]=='ROB':
                    if ROB[ranum]['Value']==None:
                        LSRs.append({'instNum': instNum,'Op': t, 'Dst':renameddest,'Tag1': '','Tag2': Ra,'Val1':None,'Val2':None,'offset':offset,'address':None,'FinalCycle':None,'MemFinalCycle':None})
                    else:
                        LSRs.append({'instNum': instNum,'Op': t,'Dst':renameddest,'Tag1': '','Tag2': '','Val1':None,'Val2':ROB[ranum]['Value'],'offset':offset,'address':None,'FinalCycle':None,'MemFinalCycle':None})
                else:
                    LSRs.append({'instNum': instNum,'Op': t,'Dst':renameddest,'Tag1': '','Tag2': '','Val1':None,'Val2':ARFint[ranum],'offset':offset,'address':None,'FinalCycle':None,'MemFinalCycle':None})

                ##rename destination
                RATfloat[inst['Fa']]=renameddest
                ROB[ROBtail]= {'instNum': instNum,'Type': t, 'Dst': inst['Fa'],'Value': None, 'Fin': False}
                ROBtail+=1
                

            elif t == 'sd':
                Fa = RATfloat[inst['Fa']]
                faName = re.split('(\d+)',Fa)
                fanum = int(faName[1])
                if faName[0]=="ROB" and raName[0]=="ROB":
                    
                    if ROB[fanum]['Value']==None and ROB[ranum]['Value']==None:
                        LSRs.append({'instNum': instNum,'Op': t, 'Dst': None, 'Tag1': Fa,'Tag2': Ra,'Val1':None,'Val2':None,'offset':offset,'address':None,'FinalCycle':None,'MemFinalCycle':None})
                    elif ROB[fanum]['Value']!=None and ROB[ranum]['Value']==None:
                        LSRs.append({'instNum': instNum,'Op': t, 'Dst':None, 'Tag1': '','Tag2': Ra,'Val1':ROB[fanum]['Value'],'Val2':None,'offset':offset,'address':None,'FinalCycle':None,'MemFinalCycle':None})
                    elif ROB[fanum]['Value']==None and ROB[ranum]['Value']!=None:
                        LSRs.append({'instNum': instNum,'Op': t, 'Dst':None, 'Tag1': Fa,'Tag2': '','Val1':None,'Val2':ROB[ranum]['Value'],'offset':offset,'address':None,'FinalCycle':None,'MemFinalCycle':None})
                    else:
                        LSRs.append({'instNum':instNum,'Op': t, 'Dst':None, 'Tag1': '','Tag2': '','Val1':ROB[fanum]['Value'],'Val2':ROB[ranum]['Value'],'offset':offset,'address':None,'FinalCycle':None,'MemFinalCycle':None})

                #Only source with ROB
                elif faName[0]=="ROB":
                    if ROB[rsnum]['Value']==None:
                        LSRs.append({'instNum':instNum,'Op': t, 'Dst':None, 'Tag1': Fa,'Tag2': '','Val1':None,'Val2':ARFint[ranum],'offset':offset,'address':None,'FinalCycle':None,'MemFinalCycle':None})
                    else:
                        LSRs.append({'instNum':instNum,'Op': t, 'Dst':None, 'Tag1': '','Tag2': '','Val1':ROB[fanum]['Value'],'Val2':ARFint[ranum],'offset':offset,'address':None,'FinalCycle':None,'MemFinalCycle':None})
                
                elif raName[0]=="ROB":

                    if ROB[rtnum]['Value']==None:
                        LSRs.append({'instNum':instNum,'Op': t, 'Dst':None, 'Tag1': '','Tag2': Ra,'Val1':ARFfloat[fanum],'Val2':None,'offset':offset,'address':None,'FinalCycle':None,'MemFinalCycle':None})
                    else:
                        LSRs.append({'instNum':instNum,'Op': t, 'Dst':None, 'Tag1': '','Tag2': '','Val1':ARFfloat[fanum],'Val2':ROB[ranum]['Value'],'offset':offset,'address':None,'FinalCycle':None,'MemFinalCycle':None})
                #both sources not in ROB
                else:
                    LSRs.append({'instNum':instNum,'Op': t, 'Dst': None, 'Tag1': '','Tag2': '','Val1':ARFfloat[fanum],'Val2':ARFint[ranum],'offset':offset,'address':None,'FinalCycle':None,'MemFinalCycle':None})

                #add sd to ROB
                ROB[ROBtail]= {'instNum': instNum,'Type': t, 'Dst': None,'Value': None, 'Fin': False}
                ROBtail+=1

            return 1


    else:
        return 0



###########################################################################################################################################





def pushInstToExec(cc,resStation,funcU,t,i,numcyclesinex):
    global timingTable
    rmIndices = []
    for j,rs in enumerate(resStation):
        if rs['instNum']==i:
            ##ld is the only instruction with only one source.  Thus, only check tag2
            if t == 'ld':
                if rs['Val2'] is not None and rs['Tag2']=='':
                ##loop through FUs to see if they are occupied
                    for fu in funcU:
                        if not fu['Occupied']:
                            fu['Type']=t
                            fu['address'] = operation(t,rs['Val2'],rs['offset'])
                            fu['Dst'] = rs['Dst']
                            fu['instNum'] = rs['instNum']
                            fu['Occupied'] = True
                            fu['FinalCycle'] = cc + numcyclesinex - 1
                            rs['FinalCycle']=fu['FinalCycle']
                            rs['address']=fu['address']
                            #rmIndices.append(j)
                            timingTable[i]['exec']=str(cc) + '-' + str(fu['FinalCycle'])
                            break
                elif rs['Val2'] is not None and rs['Tag2'] =='replaced':
                    rs['Tag2']=''
                    break

            ## all other instructions have two sources
            else:
                ##if values are ready
                if rs['Val1'] is not None and rs['Val2'] is not None and rs['Tag1']=='' and rs['Tag2']=='':
                ##loop through FUs to see if they are occupied
                    for fu in funcU:
                        if not fu['Occupied']:
                            if t == "sd":
                                fu['Type']=t
                                fu['address'] = operation(t,rs['Val2'],rs['offset'])
                                fu['Dst'] = rs['Dst']
                                fu['instNum'] = rs['instNum']
                                fu['Occupied'] = True
                                fu['FinalCycle'] = cc + numcyclesinex - 1
                                rs['FinalCycle']=fu['FinalCycle']
                                rs['address']=fu['address']
                                for ROBentry in ROB:
                                    if ROBentry['instNum']==fu['instNum']:
                                        ROBentry['Fin']=True
                                        print('ROBtrue'+str(cc))
                                #rmIndices.append(j)
                                timingTable[i]['exec']=str(cc) + '-' + str(fu['FinalCycle'])
                                break
                            else:
                                fu['Type']=t
                                fu['Value'] = operation(t,rs['Val1'],rs['Val2'])
                                fu['Dst'] = rs['Dst']
                                fu['instNum'] = rs['instNum']
                                fu['Occupied'] = True
                                fu['FinalCycle'] = cc + numcyclesinex - 1
                                fu['offset']=rs['offset']
                                rmIndices.append(j)
                                timingTable[i]['exec']=str(cc) + '-' + str(fu['FinalCycle'])
                                    
                                break
                ##dependent instructions: wait one cycle since values were just written back
                elif rs['Val1'] is not None and rs['Val2'] is not None and (rs['Tag1'] == 'replaced' or rs['Tag2'] =='replaced'):
                    rs['Tag1']=''
                    rs['Tag2']=''
                    break
                

    for index in rmIndices:
        resStation.pop(index)
    return (resStation,funcU)

def pushtoRS(t, inst, instNum, resStation, RAT, ARF):
    global ROB

    ##for branch instructions, there is no destination
    if t in ['beq','bne']:
        renameddest=None
        offset = int(inst['offset'])
    else:
        renameddest = 'ROB'+str(ROBtail)
        offset=None
    
                
    #Read RAT and dispatch in Reservation station
    rs = RAT[inst['Rs']]
    rt = RAT[inst['Rt']]
    rsName = re.split('(\d+)',RAT[inst['Rs']])
    rtName = re.split('(\d+)',RAT[inst['Rt']])

    rsnum = int(rsName[1])
    rtnum = int(rtName[1])
                
    #print(rsName)
    #print(rtName)
    ##both dependent on instructions
    if rsName[0]=="ROB" and rtName[0]=="ROB":
                    
        if ROB[rsnum]['Value']==None and ROB[rtnum]['Value']==None:
            resStation.append({'instNum': instNum,'Op': t, 'Dst': renameddest, 'Tag1': rs,'Tag2': rt,'Val1':None,'Val2':None,'offset':offset})
        elif ROB[rsnum]['Value']!=None and ROB[rtnum]['Value']==None:
            resStation.append({'instNum': instNum,'Op': t, 'Dst': renameddest, 'Tag1': '','Tag2': rt,'Val1':ROB[rsnum]['Value'],'Val2':None,'offset':offset})
        elif ROB[rsnum]['Value']==None and ROB[rtnum]['Value']!=None:
            resStation.append({'instNum': instNum,'Op': t, 'Dst': renameddest, 'Tag1': rs,'Tag2': '','Val1':None,'Val2':ROB[rtnum]['Value'],'offset':offset})
        else:
            resStation.append({'instNum':instNum,'Op': t, 'Dst': renameddest, 'Tag1': '','Tag2': '','Val1':ROB[rsnum]['Value'],'Val2':ROB[rtnum]['Value'],'offset':offset})

    #Only source with ROB
    elif rsName[0]=="ROB":
        if ROB[rsnum]['Value']==None:
            resStation.append({'instNum':instNum,'Op': t, 'Dst': renameddest, 'Tag1': rs,'Tag2': '','Val1':None,'Val2':ARF[rtnum],'offset':offset})
        else:
            resStation.append({'instNum':instNum,'Op': t, 'Dst': renameddest, 'Tag1': '','Tag2': '','Val1':ROB[rsnum]['Value'],'Val2':ARF[rtnum],'offset':offset})

    #only target with ROB
    elif rtName[0]=="ROB":

        if ROB[rtnum]['Value']==None:
            resStation.append({'instNum':instNum,'Op': t, 'Dst': renameddest, 'Tag1': '','Tag2': rt,'Val1':ARF[rsnum],'Val2':None,'offset':offset})
        else:
            resStation.append({'instNum':instNum,'Op': t, 'Dst': renameddest, 'Tag1': '','Tag2': '','Val1':ARF[rsnum],'Val2':ROB[rtnum]['Value'],'offset':offset})

    #both sources not in ROB
    else:
        resStation.append({'instNum':instNum,'Op': t, 'Dst': renameddest, 'Tag1': '','Tag2': '','Val1':ARF[rsnum],'Val2':ARF[rtnum],'offset':offset})

    #Update RAT
    if t not in ['beq','bne']:
        RAT[inst['Rd']]=renameddest                 

    return (resStation,RAT)
        
def operation(op,rs,rt):
    if op == 'add' or op=='addi':
        return int(rs + rt)
    elif op == 'add.d':
        return float(rs + rt)
    elif op == 'sub':
        return int(rs - rt)
    elif op == 'sub.d':
        return float(rs - rt)
    elif op == 'mult.d':
        return float(rs*rt)
    elif op == 'beq':
        return rs == rt
    elif op == 'bne':
        return rs != rt
    elif op == 'ld' or op == 'sd':
        return int(rs + rt)
    else:
        print("Unknown operation:",op)
        exit()

def print_stat():
    print('***************   HARDWARE STATUS  ***********')
    print()
    print_ARF()
    print()
    print_ROB()
    print()
    print_mem()
    print()


def print_ARF():
    print('------ ARF ------')
    ARFintheader = ['R'+str(i) for i in range(32)]
    ARFfloatheader = ['F'+str(i) for i in range(32)]
    print('%-16s %-9s' %('ARFint','ARFfloat'))
    print('---------------------------')
    for i in range(len(ARFint)):
        print('%-4s %-5s %-5s %-5s %-4s' %(ARFintheader[i],ARFint[i],'|',ARFfloatheader[i],ARFfloat[i]))

def print_ROB():
    print('------ ROB ------')
    print('%-10s %-5s %-4s %-4s %-4s' %('ROB','Type','Dst','Value','Fin'))
    print('-----------------------------------------')
    for i, robentry in enumerate(ROB):
        if i == ROBhead:
            print('%-10s %-5s %-4s %-4s %-4s ----Head' %('ROB'+str(i),robentry['Type'], robentry['Dst'],robentry['Value'],robentry['Fin']))
        elif i==ROBtail:
            print('%-10s %-5s %-4s %-4s %-4s ----Tail' %('ROB'+str(i),robentry['Type'], robentry['Dst'],robentry['Value'],robentry['Fin']))
        else:
            print('%-10s %-5s %-4s %-4s %-4s' %('ROB'+str(i),robentry['Type'], robentry['Dst'],robentry['Value'],robentry['Fin']))

def print_RS():
    print('------ Reservation Stations ------')
    resStationNames = ['Integer Add RS', 'FP Add RS','FP Mult RS', 'Load/Store RS']
    #{'instNum': instNum,'Op': t, 'Dst': inst['Rd'], 'Tag1': rs,'Tag2': rt,'Val1':None,'Val2':ROB[rtnum]['Value']}
    for i, rs in enumerate([IntAddRs,FPAddRs,FPMultRs,LSRs]):
        print(resStationNames[i])
        if i!=3:
            print('%-4s %-4s %-4s %-4s %-4s %-4s' %('Op','Dst','Tag1','Tag2','Val1','Val2'))
            for rsentry in rs:
                print('%-4s %-4s %-4s %-4s %-4s %-15s' %(rsentry['Op'],rsentry['Dst'],rsentry['Tag1'], rsentry['Tag2'], rsentry['Val1'], rsentry['Val2']))
        else:
            print('%-4s %-4s %-4s %-4s %-4s %-4s %-4s %-4s' %('Op','Dst','Tag1','Tag2','Val1','Val2','offset','address'))
            for rsentry in rs:
                print('%-4s %-4s %-4s %-4s %-4s %-4s %-4s %-4s' %(rsentry['Op'],rsentry['Dst'],rsentry['Tag1'], rsentry['Tag2'], rsentry['Val1'], rsentry['Val2'],rsentry['offset'],rsentry['address']))
        print()

def print_timingTable():
    print('------ Timing Table ------')
    print('%-4s %-20s %-4s %-8s %-6s %-4s %-4s' %('#','Instruction','Iss','Ex','Mem','WB','Commit'))
    print('---------------------------------------------------------------')
    #{'InstNum':instNum,'Type':nextInst['Type']','Instruction':nextInst,'iss':cc,'exec':None,'mem':None,'wb':None,'c':None}
    for entry in timingTable:
        #'Type': cmd,'Fa':Fa,'offset':offset,'Ra':reg
        if entry['Type'] in ['ld','sd']:
            instructionname  = entry['Instruction']['Type']+' '+entry['Instruction']['Fa']+' '+entry['Instruction']['offset']+'('+entry['Instruction']['Ra']+')'
        elif entry['Type'] in ['beq','bne']:
            instructionname  = entry['Instruction']['Type']+' '+entry['Instruction']['Rs']+', '+entry['Instruction']['Rt']+', '+entry['Instruction']['offset']
        else:
            instructionname  = entry['Instruction']['Type']+' '+entry['Instruction']['Rd']+' '+entry['Instruction']['Rs']+' '+entry['Instruction']['Rt']
            
        print('%-4s %-20s %-4s %-8s %-6s %-4s %-4s' %(entry['InstNum'],instructionname,entry['iss'],entry['exec'],entry['mem'],entry['wb'],entry['c']))

          
def print_mem():
    print('------ Memory ------')
    print('%-5s | %-5s' %('Address','Value'))
    for i in range(len(Memory)):
        print('%-5s | %-5s' %(i,Memory[i]))

    
                
if __name__ == '__main__':
    main()
