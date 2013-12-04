#!/usr/bin/env python
import string
import datetime as DT
from matplotlib import pyplot as plt
from matplotlib.dates import date2num

timeouts = {}
reassocs = {}

f = open('logs/host_timeouts.log','r')
for line in f.readlines():
    vals = string.split(line.rstrip(),' ')
    node = vals[2]
    x1 =  vals[-1].find("secs:")
    time = string.split(line.rstrip(),'|')[0]
    duration = int(vals[-1][x1+5:-1])
    try:
        timeouts[node].append((time,duration))
    except KeyError:
        timeouts[node] = [(time,duration)]
f.close()

f = open('logs/reassoc_full.log','r')
for line in f.readlines():
    node = string.split(line.rstrip(),' ')[-1]
    time = string.split(line.rstrip(),'|')[0]
    try:
        reassocs[node].append(time)
    except KeyError:
        reassocs[node] = [time]
f.close()

for node in reassocs.keys():
    x = [DT.datetime.strptime(t,"%Y-%m-%d %H:%M:%S,%f") for t in reassocs[node]]
    y = [1]*len(x)
    #y = [t[1] for t in reassocs[node]]
    fig = plt.figure()
    plt.plot(x,y,'.',label=node)
    for con in timeouts[node]:
        end = DT.datetime.strptime(con[0],"%Y-%m-%d %H:%M:%S,%f")
        start = end - DT.timedelta(seconds=con[1])
        plt.plot([start,end],[2,2],'b-o')
    plt.ylim([0,3])
    plt.legend()

plt.show()
print reassocs.keys()
print timeouts.keys()


#data = [(DT.datetime.strptime('2010-02-05', "%Y-%m-%d"), 123),
#        (DT.datetime.strptime('2010-02-19', "%Y-%m-%d",678)]

#x = [date2num(date) for (date, value) in data]
#y = [value for (date,value) in data]

#fig = plt.figure()
