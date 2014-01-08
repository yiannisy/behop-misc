#!/usr/bin/env python
import string
import sys
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams.update({'font.size': 22})
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
    #('gates-behop-complete','A','b-'),
    #('studio5-lwapp-indoors','B','r-'),
    #('caltrain-24ghz-40mhz-1_iperf','C','g-'),
    #'gates-behop-linux-complete',
    #('gates-wrt-complete','A'),
    #('boonies-wrt-complete','A+','b--'),
    #('studio5-lwapp', 'B+','r--'),
    #('gates-meraki-2_iperf','C+','g--'),
    #('gates-netgear-complete','C++','g-.'),

    #('gates-netgear-behop','C+','g--'),
    #('behop-full-5ghz','C+','g--'),


    #'malakas_auto_dl',
    #'malakas_no_col_auto_dl',
    #'malakas_no_nec_auto_dl', 
    #'malakas_no_nec_1_auto_dl',
    #'malakas_no_nec_no_col_auto_dl',
    #'openwrt-vanilla',
    #'openwrt-vanilla-1',
    #'tp_link_auto_dl',

    #'pi_meraki_auto_dl',
    #'pi_openwrt_vanilla_auto_dl'
    ]

fig = pylab.figure(figsize=(16,12))
lns = None
for log in logs:
    iperf_log = "./logs/%s.log" % log[0]
    f = open(iperf_log,'r')
    throughput = []
    for line in f.readlines():
        vals = string.split(line,',')
        kbps = int(vals[-1])/1000000.0
        throughput.append(kbps)

    x = sorted(throughput)
    y = [(float(i + 1) / len(x)) for i in range(len(x))]
    if lns:
        lns += pylab.plot(x,y,log[2],label=log[1])
    else:
        lns = pylab.plot(x,y, log[2],label=log[1])
    f.close()

#labels = [l.get_label() for l in lns]
pylab.xlabel('TCP Goodput (Mbps)')
#pylab.xscale('log')
pylab.ylabel('CDF')
#pylab.legend(lns, labels,loc=4)
pylab.legend()
pylab.grid()
pylab.xlim([0,200])
pylab.title('WiFi Performance')
pylab.savefig("%s.png" % output)
