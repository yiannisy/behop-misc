#!/usr/bin/env python
import string
import sys
import os
from collections import defaultdict
from util import plot_cdf

s4_rtts = defaultdict(list)
s4_path="./rtt-analysis/studio4_rtts/"
s5_rtts = defaultdict(list)
s5_path="./rtt-analysis/studio5_rtts/"

to_plot = []
files = os.listdir(s4_path)
for fname in files:
    fname = s4_path + fname
    f = open(fname,'r')
    for l in f.readlines():
        ip,vals = string.split(l.rstrip(),',')
        ts,seq,rtt = string.split(vals,' ')
        s4_rtts[ip].append(float(rtt)/1000.0)
    to_plot.append([s4_rtts[ip],'S4','g'])

files = os.listdir(s5_path)
for fname in files:
    fname = s5_path + fname
    f = open(fname,'r')
    for l in f.readlines():
        ip,vals = string.split(l.rstrip(),',')
        ts,seq,rtt = string.split(vals,' ')
        s5_rtts[ip].append(float(rtt)/1000.0)
    to_plot.append([s5_rtts[ip],'S5','r'])


plot_cdf(to_plot,'rtts',legend=False,xlogscale=True,title='RTTs',xlabel='time (ms)',ylabel='CDF',alpha=0.5,xlim=[0.1,10**5])

print files
sys.exit(0)
fname=sys.argv[1]
print fname

f = open(fname,'r')
for line in f.readlines():
    vals = string.split(line,' ')
    tstamp = float(vals[0])
    rtt = float(vals[2])
    rtts.append(rtt)
f.close()

pylab.figure()
x = sorted(rtts)
y = [(float(i+1)/len(x)) for i in range(len(x))]
pylab.plot(x,y)
pylab.xscale('log')
pylab.xlabel('RTT (msecs)')
pylab.ylabel('CDF')
pylab.title('RTT CDF (all nodes)')
pylab.grid()
pylab.show()
