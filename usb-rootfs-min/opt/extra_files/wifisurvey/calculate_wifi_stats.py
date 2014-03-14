#!/usr/bin/env python
import string
from datetime import datetime,timedelta
import sys

LAST_FNAME="/var/run/last_wifistats.log"
CUR_FNAME="/var/run/cur_wifistats.log"
try:
    f1 = open(LAST_FNAME,'r')
    f2 = open(CUR_FNAME,'r')
except:
    sys.exit(0)

intfs = {'mon0':{},'mon1':{},'wlan0':{},'wlan1':{}}

for l in f1.readlines():
    ts_last,dpid,intf,rx_pkts,tx_pkts,rx_bytes,tx_bytes=string.split(l,',')
    intfs[intf]['rx_pkts_last'] = int(rx_pkts)
    intfs[intf]['tx_pkts_last'] = int(tx_pkts)
    intfs[intf]['rx_bytes_last'] = int(rx_bytes)
    intfs[intf]['tx_bytes_last'] = int(tx_bytes)

for l in f2.readlines():
    ts_cur,dpid,intf,rx_pkts,tx_pkts,rx_bytes,tx_bytes=string.split(l,',')
    intfs[intf]['rx_pkts_cur'] = int(rx_pkts)
    intfs[intf]['tx_pkts_cur'] = int(tx_pkts)
    intfs[intf]['rx_bytes_cur'] = int(rx_bytes)
    intfs[intf]['tx_bytes_cur'] = int(tx_bytes)

ts_last = datetime.strptime(ts_last,'%Y.%m.%d-%H:%M:%S')
ts_cur = datetime.strptime(ts_cur,'%Y.%m.%d-%H:%M:%S')

#only calculate if we this is a 1-minute interval
if (ts_cur - ts_last < timedelta(minutes=2)):
    for intf in intfs.keys():
        print "%s,%s,%s,%d,%d,%d,%d" % (datetime.now().strftime("%Y.%m.%d-%H:%M:%S"),dpid,intf,
                                        intfs[intf]['rx_pkts_cur'] - intfs[intf]['rx_pkts_last'],
                                        intfs[intf]['tx_pkts_cur'] - intfs[intf]['tx_pkts_last'],
                                        intfs[intf]['rx_bytes_cur'] - intfs[intf]['rx_bytes_last'],
                                        intfs[intf]['tx_bytes_cur'] - intfs[intf]['tx_bytes_last'])

f1.close()
f2.close()

