#!/usr/bin/env python
import string
import sys
import matplotlib
matplotlib.use('Agg')
import pylab
#f1 = open('_snr.log','r')
#f2 = open('_times.log','r')
#f1_lines = f1.readlines()
#f2_lines = f2.readlines()
#for l1,l2 in zip(f1_lines, f2_lines):
#    l1 = l1.strip()
#    l2 = l2.strip()
#    print l2[10:19], l1[-3:]
#f1.close()
#f2.close()

output = sys.argv[1]

def time_str_to_sec(timestr,base,offset=0):
    time_vals = string.split(timestr,':')
    time = 3600*int(time_vals[0])+60*int(time_vals[1])+int(time_vals[2])
    time = time - base - offset
    return time

logs = [
    'malakas_auto_dl',
    #'malakas_no_col_auto_dl',
    #'malakas_no_nec_auto_dl', 
    'malakas_no_nec_1_auto_dl',
    'malakas_no_nec_no_col_auto_dl',
    #'openwrt-vanilla',
    'openwrt-vanilla-1',
    'tp_link_auto_dl',
    'meraki_auto_dl'
    ]

fig = pylab.figure(figsize=(16,12))
lns = None
for log in logs:
    wifi_log = "%s_wireless.log" % log
    f = open(wifi_log,'r')
    latencies = []
    for line in f.readlines()[1:-1]:
        vals = string.split(line,'|')
        print vals[1]
        try:
            lat = float(vals[1])
        except:
            lat = -1.0
        latencies.append(lat)
    if lns:
        lns += pylab.stem(range(0, len(latencies)), latencies,'-.', label=log)
    else:
        lns = pylab.stem(range(0, len(latencies)), latencies, '-.')
    f.close()

#labels = [l.get_label() for l in lns]
pylab.xlabel('time (s)')
pylab.ylabel('Latency (ms)')
#pylab.legend(lns, labels)
pylab.grid()
pylab.title('WiFi Latency (%s)' % output)
pylab.savefig("%s.pdf" % output)
