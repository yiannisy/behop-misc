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

    for i in range(0,60): #int(packets[-1][0])):
        sec_packets = [p for p in packets if p[0] > i and p[0] < i+1]
        durations = {'DATA':0,'MGMT':0,'CTRL':0}
        bytes = {'DATA':0,'MGMT':0,'CTRL':0}
        
        plt.figure()
        currentAxis = plt.gca()
        colors={'MGMT':'red','CTRL':'blue','DATA':'green'}
        offset={'MGMT':1,'CTRL':2,'DATA':3}
        idx = 0
        for pkt in sec_packets:
            if pkt[2] == -1:
                print "unknown type"
                continue
            currentAxis.add_patch(Rectangle((pkt[0],offset[pkt[2]]), pkt[1]*10**(-6), 1, facecolor=colors[pkt[2]],
                                            aa=True,edgecolor='none'))
            durations[pkt[2]] += pkt[1]
            bytes[pkt[2]] += 0
            #if idx < 20:
            #    print "%d,%f,%d,%s,%s,%d" % (idx,pkt[1],pkt[4],pkt[2],pkt[3],pkt[5])
            #    idx += 1
            
        
        plt.ylim([0,5])
        plt.xlim([sec_packets[0][0],sec_packets[-1][0]])
        print "sec:%d,efficiency:%f,bytes:%d,packets:%d" % (i,sum(durations.values())*10**-6,sum(bytes.values()),len(sec_packets))
        pylab.savefig('timeline_%d.png' % i)
    #print durations


#rates = [p[4] for p in packets]
#print set(rates)
#for r in set(rates):
#   print r,len([_r for _r in rates if _r == r])
