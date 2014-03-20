#!/usr/bin/env python
import string
import sys
import os
from collections import defaultdict
from util import plot_cdf

s4_rtts = defaultdict(list)
s4_path="./rtt-analysis/studio4_rtts/"
s4_path="./rtt-2014-03-16/"
s5_rtts = defaultdict(list)
s5_path="./rtt-2014-03-18/"

to_plot = []
files = os.listdir(s4_path)
files = [f for f in files if f.startswith("rtt_10.30")]
for fname in files:
    fname = s4_path + fname
    f = open(fname,'r')
    line = f.readlines()[0]
    ip,vals = string.split(line.rstrip(),',')
    ts,seq,rtt = string.split(vals,' ')
    ts = float(ts)
    ts_start = ts
    lines = f.readlines()
    while True:
        while ts < ts_start + 60:
            if len(lines) == 0:
                break
            l = lines.pop(0)
            ip,vals = string.split(l.rstrip(),',')
            ts,seq,rtt = string.split(vals,' ')
            ts = float(ts)
            s4_rtts[ip].append(float(rtt)/1000.0)
        to_plot.append([s4_rtts[ip],'Multiple-Channels','g'])
        ts_start = ts
        if len(lines) == 0:
            break

files = os.listdir(s5_path)
files = [f for f in files if f.startswith("rtt_10.30")]
for fname in files:
    fname = s5_path + fname
    f = open(fname,'r')
    line = f.readlines()[0]
    ip,vals = string.split(line.rstrip(),',')
    ts,seq,rtt = string.split(vals,' ')
    ts = float(ts)
    ts_start = ts
    lines = f.readlines()
    while True:
        while ts < ts_start + 60:
            if len(lines) == 0:
                break
            l = lines.pop(0)
            ip,vals = string.split(l.rstrip(),',')
            ts,seq,rtt = string.split(vals,' ')
            ts = float(ts)
            s5_rtts[ip].append(float(rtt)/1000.0)
        to_plot.append([s5_rtts[ip],'Single-Channel','r'])
        ts_start = ts
        if len(lines) == 0:
            break

plot_cdf(to_plot,'rtts',legend=False,xlogscale=True,title='RTTs',xlabel='PDT (ms)',ylabel='CDF',alpha=0.5,xlim=[0.1,10**5])

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
