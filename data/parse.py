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

ctrl_log = sys.argv[1]
laptop_log = sys.argv[2]
output = sys.argv[3]

def time_str_to_sec(timestr,base,offset=0):
    time_vals = string.split(timestr,':')
    time = 3600*int(time_vals[0])+60*int(time_vals[1])+int(time_vals[2])
    time = time - base - offset
    return time
    

f = open(ctrl_log,'r')
cur_snrs = []
max_snrs = []
sta_snrs = []
ap_snrs = {}
pings = []
time_base = None
for line in f.readlines():
    vals = string.split(line,' ')
    #print vals
    #print vals[0],vals[6], vals[7], vals[11], vals[12]
    time = vals[0][1:-1]    
    time_vals = string.split(time,':')
    time = 3600*int(time_vals[0])+60*int(time_vals[1])+int(time_vals[2])
    if time_base == None:
        time_base = time
    time = time-time_base
    cur_snr = int(vals[6])
    cur_snrs.append((time,cur_snr))
    if (len(vals) > 15):
        _snrs = []
        for item in vals[15:]:
            dpid,snr = string.split(item,'->')
            snr = int(snr)
            if dpid not in ap_snrs.keys():
                ap_snrs[dpid] = []
            ap_snrs[dpid].append((time,snr))
            _snrs.append(snr)
    #cur_dpid = vals[7][1:-1]
    #max_snr = int(vals[11])
    #max_dpid = vals[12][1:-2]
    #cur_snrs.append(cur_snr)
    #max_snrs.append(max_snr)
        max_snrs.append((time, max(_snrs)))
f.close()
#sys.exit(0)
f = open(laptop_log,'r')
l_time_base = None
for line in f.readlines():
    vals = string.split(line,' ')
    time_str = vals[3]
    if l_time_base == None:
        l_time_base = time_str_to_sec(time_str, 0) - 7
        time = 0
    else:
        time = time_str_to_sec(time_str, l_time_base)
    sta_snr = int(vals[-5])
    sta_snr = 90 + sta_snr
    sta_snrs.append((time,sta_snr))
    if (string.find(line,'icmp_seq') != -1):
        ping_time = float(vals[12][5:])
    else:
        ping_time = 1000

    pings.append((time, ping_time))
    print time, sta_snr, ping_time
        
        
f.close()
#f = open('tracking_ping.log','r')
#for line in f.readlines():
#    if line.startswith("none") or line.startswith("Request"):
#        pings.append(0)
#    else:
#        vals = string.split(line,' ')
#        pings.append(float(vals[6][5:]))
fig = pylab.figure(figsize=(16,12))
ax = fig.add_subplot(111)
lns = ax.plot([s[0] for s in cur_snrs],[s[1] for s in cur_snrs], 'r-', label='cur_snr (AP)')
#for dpid in ap_snrs.keys():
#    lns += ax.plot([s[0] for s in ap_snrs[dpid]], [s[1] for s in ap_snrs[dpid]], '--', label='%s' % dpid)
lns += ax.plot([s[0] for s in max_snrs], [s[1] for s in max_snrs], '--',label='max_snr (AP)')
lns += ax.plot([s[0] for s in sta_snrs], [s[1] for s in sta_snrs], 'c-', label='sta_snr (STA)')
ax2 = ax.twinx()
#lns += ax2.stem([p[0] for p in pings], [p[1] for p in pings], 'mx',label='ping (STA)')
ax2.stem([p[0] for p in pings], [p[1] for p in pings], 'm-.',label='ping (STA)')
labels = [l.get_label() for l in lns]
ax.set_xlabel('time (s)')
ax.set_ylabel('SNR (dB)')
ax2.set_ylabel('ping time (ms)')
ax.set_ylim([0,60])
ax2.set_ylim([0,1000])
#ax.annotate('A->B', xy=(74, 27),  xycoords='data',
#                xytext=(50, -100), textcoords='offset points',
#                arrowprops=dict(arrowstyle="->")
#                )
#ax.annotate('B->A', xy=(104, 26),  xycoords='data',
#                xytext=(50, -100), textcoords='offset points',
#                arrowprops=dict(arrowstyle="->")
#                )

pylab.legend(lns, labels)
pylab.grid()
pylab.title('WiFi Handover (%s)' % output)
pylab.savefig("%s.pdf" % output)
