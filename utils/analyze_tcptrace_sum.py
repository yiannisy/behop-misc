#!/usr/bin/env python
import string,sys
import re

f = open('.tmp/tcptrace_summary.txt','r')
for line in f.readlines()[7:]:
    if line.find('unidirectional') != -1:
        continue
    p = re.compile(r'(\w+.\w+.\w+.\w+):\w+ - (\w+.\w+.\w+.\w+):\w+ \((\w+)2(\w+)\)')
    m = p.search(line)
    if m:
        ip_src = m.group(1)
        ip_dst = m.group(2)
        flow_src = m.group(3)
        flow_dst = m.group(4)
        if ip_src.startswith("10.30") and ip_dst.startswith("10.30"):
            print "SRC - DST both in network --- skipping..."
            print ip_src,ip_dst,flow_src,flow_dst
            continue
        if ip_src.startswith("10.30"):
            host = ip_src
            end = ip_dst
            flow = flow_dst + "2" + flow_src + "_rttraw.dat"
        elif ip_dst.startswith("10.30"):
            flow = flow_src + "2" + flow_dst + "_rttraw.dat"
            host = ip_dst
            end = ip_src
        rtt_fname = ".tmp/" + flow
        host_fname = '.tmp/rtt_%s.log' % host
        try:
            f_rtt = open(rtt_fname,'r')
            f_host = open(host_fname,'a+')
        except:
            print "cannot find file (%s,%s)" % (rtt_fname,host_fname)
            continue
        print "Analyzing flow for %s (%s)" % (host,flow)
        for line in f_rtt.readlines():
            f_host.write(line)
        f_rtt.close()
        f_host.close()
        
f.close()
sys.exit(0)
