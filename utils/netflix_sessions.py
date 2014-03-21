#!/usr/bin/env python
import sys,string
from datetime import datetime,timedelta

pst = timedelta(hours=8)
pdt = timedelta(hours=7)

tz_change = datetime(2014,3,9,2,0)
fname = sys.argv[1]
f = open(fname,'r')
sessions = {}


for l in f.readlines():
    if l.startswith("T 201"):
        last_ts = string.split(l,' ')[1:3]
        last_ts_str = "%s %s" % (last_ts[0],last_ts[1])
        last_ts_str = string.split(last_ts_str,'.')[0]
        raw_ts = datetime.strptime(last_ts_str,"%Y/%m/%d %H:%M:%S")
        if raw_ts < tz_change:
            ts = raw_ts + pst
        else:
            ts = raw_ts + pdt
    if l.startswith("GET "):
        vals = string.split(l,"&")
        p = [val for val in vals if val.startswith("p=5.")]
        if len(p) > 0:
            p = string.split(p[0],' ')[0]
            if p not in sessions.keys():
                sessions[p] = ts

sorted_sessions = sorted(sessions.items(),key=lambda x:x[1])
print "\n".join(["%s,%s" % (s[1],s[0]) for s in sorted_sessions])
