#!/usr/bin/env python
# Requires dpkt-1.7 for radiotap headers.
import sys
import dpkt
#import pcap
import matplotlib
matplotlib.use('Agg')
import pylab
import pickle
from ieee80211_params import *
from plot_timeline import *

rates_n = {'40_sgi':{0x0:15,0x1:30,0x2:45,0x3:60,0x4:90,0x5:120,0x6:135,0x7:150,
                     0x8:30,0x9:60,0xa:90,0xb:120,0xc:180,0xd:240,0xe:270,0xf:300},
           '40_lgi':{0x0:13.5,0x1:27,0x2:40.5,0x3:54,0x4:81,0x5:108,0x6:121.5,0x7:135,
                     0x8:27,0x9:54,0xa:81,0xb:108,0xc:162,0xd:216,0xe:243,0xf:270},
           '20_sgi':{0x0:7.2,0x1:14.4,0x2:21.7,0x3:28.9,0x4:43.3,0x5:57.8,0x6:65,0x7:72.2,
                     0x8:14.4,0x9:28.9,0xa:43.3,0xb:57.8,0xc:86.7,0xd:115.6,0xe:130,0xf:144.4},
           '20_lgi':{0x0:6.5,0x1:13,0x2:19.5,0x3:26,0x4:39,0x5:52,0x6:58.5,0x7:65,
                     0x8:13,0x9:26,0xa:39,0xb:52,0xc:78,0xd:104,0xe:117,0xf:130}
           }

RT_HDR_LEN=13

def plot_timeline(packets):
    pylab.figure()
    for pkt in packets:
        pylab.axhspan(1,2,pkt[0],pkt[0]+pkt[1])
    pylab.savefig('timeline.png')

def DIV_ROUND_UP(n,d):
    return (((n) + (d) -1)/(d))

def ieee80211_is_erp_rate(phymode, rate):
    '''check if this is an extended rate'''
    if (phymode & PHY_FLAG_G):
        if (rate != 10 and rate != 20 and rate != 55
            and rate != 110):
            return 1
    return 0

def ieee80211_frame_duration(phymode,length,rate,short_preamble,
                             shortslot,pkt_type,pkt_stype,qos_class,retries):
    '''porting kernel's function to python.'''
    #logger.debug("phymode : %d, length:%d,rate:%d,short_preamble:%x,shortslot:%x,pkt_type:%x,qos_class:%x,retries:%d" % (phymode,length,rate,short_preamble,shortslot,pkt_type,qos_class,retries))
    if(phymode == PHY_FLAG_A) or (ieee80211_is_erp_rate(phymode,rate)):
        # we are in OFDM mode. Look at ieee80211_util.c for details.
        # logger.debug("OFDM mode")
        sifs = 16
        slottime = 9
        dur = 16
        dur += 4
        dur += 4*DIV_ROUND_UP((16+8*(length+4)+6), 4*rate)
    else:
        #CCK mode
        #logger.debug("CCK mode")
        sifs =10
        if (shortslot==True): 
            slottime = 9
        else: 
            slottime = 20
        if (short_preamble == True):
            dur = 72+24
        else:
            dur = 144+48
        dur += DIV_ROUND_UP(8*(length+4)*10,rate)
    if (pkt_type == IEEE80211_FTYPE_CTRL) and ((pkt_stype == IEEE80211_STYPE_CTS) or (pkt_stype == IEEE80211_STYPE_ACK)):
        dur += sifs
    elif (pkt_type == IEEE80211_FTYPE_MGMT) and (pkt_stype == IEEE80211_STYPE_BEACON):
        dur += sifs + (2*slottime)
        dur += (slottime*1.0)/2.0
    elif pkt_type == IEEE80211_FTYPE_DATA:
        dur += sifs
    # store this QoS
    #elif (pkt_type == IEEE80211_DATA):
    #    dur += sifs + (ac_to_aifs[ac]*slottime)
    #    dur += get_cw_time(ac_to_cwmin[ac], ac_to_cwmax[ac], retries,slottime)
    else:
        dur += sifs + (2*slottime)
        #dur += get_cw_time(4,10,retries,slottime)
    if (pkt_type == IEEE80211_STYPE_CTS):
        last_was_cts = 1
    else:
        last_was_cts = 0
        
    return dur

def ieee80211_frame_duration_simple(phymode,length,rate,short_preamble,
                                    shortslot,pkt_type,pkt_stype,qos_class,retries):
    return length*8/float(rate)


def ieee80211_ftype(pkt_type):
    if (pkt_type == IEEE80211_FTYPE_MGMT):
        return "MGMT"
    elif (pkt_type == IEEE80211_FTYPE_CTRL):
        return "CTRL"
    elif (pkt_type == IEEE80211_FTYPE_DATA):
        return "DATA"
    else: 
        print "unknown ftype : %x" % pkt_type
        sys.exit(0)
        return -1

def ieee80211_stype(pkt_stype):
    if (pkt_stype == IEEE80211_STYPE_CTS):
        return "CTS"
    elif (pkt_stype == IEEE80211_STYPE_ACK):
        return "ACK"
    elif (pkt_stype == IEEE80211_STYPE_BEACON):
        return "BEACON"
    elif (pkt_stype == IEEE80211_STYPE_DATA):
        return "DATA"
    elif (pkt_stype == IEEE80211_STYPE_BLOCK_ACK):
        return "BLOCK_ACK"
    elif (pkt_stype == IEEE80211_STYPE_PROBE_REQ):
        return "PROBE_REQ"
    elif (pkt_stype == IEEE80211_STYPE_PROBE_RES):
        return "PROBE_RES"
    elif (pkt_stype == IEEE80211_STYPE_AUTH):
        return "AUTH"
    else: 
        return "-1,%s" % (pkt_stype)

f = open(sys.argv[1])
pcap = dpkt.pcap.Reader(f)

durs = []
second_start = -1
i= 1
packets = []

for ts,buf,buf_len in pcap:
    if second_start < 0:
        second_start = ts
    rt = dpkt.radiotap.Radiotap(buf)
    rt_hdr_len = rt.length >> 8
    #print dir(rt)
    #sys.exit()
    # radiotap doesn't parse this correctly, so hardcode it here.
    try:
        wlan_pkt = dpkt.ieee80211.IEEE80211(buf[rt_hdr_len:])
    except dpkt.dpkt.NeedData:
        print "%d. cannot decode packet---skipping..." % i
        i+= 1
        continue
    ftype = ieee80211_ftype(wlan_pkt.type)
    stype = ieee80211_stype(wlan_pkt.subtype)

    if (rt.rx_flags_present and rt.present_flags and rt.htinfo_present):
        #print "htinfo : %08x,%x,%08x,%08x,%x,%x,%x" % (rt.present_flags, rt.htinfo_present,rt.htinfo.mcs,
        #                                               rt.htinfo.mcs_info,rt.htinfo.mcs_index,
        #                                               rt.ant.index,rt.rx_flags.val)
                                                       
        bw = rt.htinfo.mcs_info & 0x3
        sgi = rt.htinfo.mcs_info & 0x4
        if bw == 1:
            mcs_category = '40_'
        else:
            mcs_category = '20_'
        if sgi:
            mcs_category = mcs_category + 'sgi'
        else:
            mcs_category = mcs_category + 'lgi'
        rate = rates_n[mcs_category][rt.htinfo.mcs_index]
    elif (not rt.rx_flags_present and not rt.rate_present):
        rate = 300
    elif rt.rate_present:
        # rates are in 500kbps increments.
        rate = int(rt.rate.val)/2
    else:
        # set rate to the lowest n rate when we don't know what it is.
        #print "cannot extract rate value."
        rate = 65
    if rt.flags_present:
        flags = rt.flags.val
    else:
        flags = 0 
        #sys.exit(0)
    #if wlan_pkt.type == IEEE80211_FTYPE_DATA:
        #print "packet is not data %d" % (wlan_pkt.type)
    #    continue
    duration = ieee80211_frame_duration_simple(flags & PHY_FLAG_MODE_MASK, buf_len - rt_hdr_len,
                             rate, flags & PHY_FLAG_SHORTPRE,
                             0, wlan_pkt.type,wlan_pkt.subtype, 0,wlan_pkt.retry)
    durs.append(duration)
    packets.append((ts,duration,ftype,stype,rate,buf_len-rt_hdr_len))
    #print "%d. %f,%d,%s,%s" % (i,ts, duration, ftype, stype)     
    i+= 1

f.close()            
process_durs(packets)

f = open('packets.pkl','wb')        
pickle.dump(packets,f)
f.close()
#plot_timeline(packets)
