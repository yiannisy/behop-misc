#!/usr/bin/env python

import matplotlib
#matplotlib.use('Agg')
import sys
import string
import pylab

fname_a = sys.argv[1]
fname_b = sys.argv[2]
f1 = open(fname_a,'r')
f2 = open(fname_b,'r')
x1 = []
x2 = []
for f,x in zip((f1,f2),(x1,x2)):
    for line in f.readlines():
        vals = {}
        for val in string.split(line,','):
            _v = string.split(val,':')
            vals[_v[0]] = float(_v[1])
        x.append(vals)
        
pylab.figure(figsize=(16,12))
pylab.subplot(4,1,1)
pylab.plot([_x['sec'] for _x in x1],[_x['load'] for _x in x1],label='2G')
pylab.plot([_x['sec'] for _x in x2],[_x['load'] for _x in x2],label='5G')
pylab.ylabel('util (%)')
pylab.title('load')
pylab.legend()
pylab.subplot(4,1,2)
pylab.plot([_x['sec'] for _x in x1],[_x['data_bytes']/float(1000) for _x in x1],label='2G')
pylab.plot([_x['sec'] for _x in x2],[_x['data_bytes']/float(1000) for _x in x2],label='5G')
pylab.ylabel('Transfer (KB)')
pylab.title('transfer')
pylab.legend()
pylab.subplot(4,1,3)
pylab.plot([_x['sec'] for _x in x1],[_x['raw_efficiency']*8 for _x in x1],label='2G')
pylab.plot([_x['sec'] for _x in x2],[_x['raw_efficiency']*8 for _x in x2],label='5G')
pylab.ylabel('efficiency (bits/usec)')
pylab.title('raw-effic')
pylab.legend()
pylab.subplot(4,1,4)
pylab.plot([_x['sec'] for _x in x1],[_x['data_efficiency']*8 for _x in x1],label='2G')
pylab.plot([_x['sec'] for _x in x2],[_x['data_efficiency']*8 for _x in x2],label='5G')
pylab.xlabel('time (s)')
pylab.ylabel('efficiency (bits/usec)')
pylab.legend()
pylab.title('data-effic')
pylab.show()

f1.close()
f2.close()
    
