#!/usr/bin/env python

import matplotlib
#matplotlib.use('Agg')
import sys
import string
import pylab

fname = sys.argv[1]
f = open(fname,'r')
x = []
for line in f.readlines():
    vals = {}
    for val in string.split(line,','):
        _v = string.split(val,':')
        vals[_v[0]] = float(_v[1])
    x.append(vals)

pylab.figure()
pylab.subplot(3,1,1)
pylab.plot([_x['sec'] for _x in x],[_x['load'] for _x in x],label='load')
pylab.legend()
pylab.subplot(3,1,2)
pylab.plot([_x['sec'] for _x in x],[_x['raw_efficiency']*8 for _x in x],label='a_raw')
pylab.legend()
pylab.subplot(3,1,3)
pylab.plot([_x['sec'] for _x in x],[_x['data_efficiency']*8 for _x in x],label='a_data')
pylab.legend()
pylab.show()
    
