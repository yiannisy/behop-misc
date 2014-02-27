#!/usr/bin/env python

import pickle
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import pylab


someX, someY = 2, 3

def process_durs(packets):
    #f = open('packets.pkl','rb')
    #packets = pickle.load(f)
    #f.close()

    baseline = packets[0][0]
    packets = [(p[0]-baseline,p[1],p[2],p[3],p[4],p[5]) for p in packets]


    for i in range(0,11,2): #int(packets[-1][0])):
        sec_packets = [p for p in packets if p[0] > i and p[0] < i+2]

        axes = plt.figure(figsize=(12,8),dpi=300).add_subplot(111)
        currentAxis = plt.gca()
        colors={'MGMT':'red','CTRL':'blue','DATA':'green'}
        offset={'MGMT':1,'CTRL':2,'DATA':3}
        durations = {'DATA':0,'MGMT':0,'CTRL':0}
        bytes = {'DATA':0,'MGMT':0,'CTRL':0}
        counts = {'DATA':0,'MGMT':0,'CTRL':0}

        idx = 0
        for pkt in sec_packets:
            if pkt[2] == -1:
                print "unknown type"
                continue
            currentAxis.add_patch(Rectangle((pkt[0],offset[pkt[2]]), pkt[1]*10**(-6), 1, facecolor=colors[pkt[2]],
                                            aa=True,edgecolor='none'))
            durations[pkt[2]] += pkt[1]
            bytes[pkt[2]] += pkt[5]
            counts[pkt[2]] += 1
            #if idx < 20:
            #    print "%d,%f,%d,%s,%s,%d" % (idx,pkt[1],pkt[4],pkt[2],pkt[3],pkt[5])
            #    idx += 1
            
        plt.plot([0],[0],'r.',label='mgmt')
        plt.plot([0],[0],'g.',label='data')
        plt.plot([0],[0],'b.',label='ctrl')
        plt.ylim([0,5])
        plt.xlim([sec_packets[0][0],sec_packets[-1][0]])
        print "sec:%d,load:%f,data_efficiency:%f,raw_efficiency:%f,bytes:%d,data_bytes:%d,packets:%d" % (i,sum(durations.values())*10**-6,
                                                                                                         bytes['DATA']/sum(durations.values()),
                                                                                                         sum(bytes.values())/sum(durations.values()),                                                                    
                                                                                                         
                                                                                                         sum(bytes.values()),bytes['DATA'],len(sec_packets))
        pylab.legend()
        pylab.xlabel('time (s)')
        axes.set_yticks([1.5,2.5,3.5])
        axes.set_yticklabels(['mgmt','ctrl','data'])
        pylab.title('Air-Timeline')
        pylab.savefig('timeline_%d.png' % i)




#print set(rates)
#for r in set(rates):
#   
