#!/usr/bin/env python
# Requires dpkt-1.7 for radiotap headers.
import sys
import dpkt
import pcap
from ieee80211_params import *

RT_HDR_LEN=34

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

def ieee80211_ftype(pkt_type):
    if (pkt_type == IEEE80211_FTYPE_MGMT):
        return "MGMT"
    elif (pkt_type == IEEE80211_FTYPE_CTRL):
        return "CTRL"
    elif (pkt_type == IEEE80211_FTYPE_DATA):
        return "DATA"
    else: 
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
for ts,buf,buf_len in pcap:
    if second_start < 0:
        second_start = ts
    rt = dpkt.radiotap.Radiotap(buf)
    # radiotap doesn't parse this correctly, so hardcode it here.
    wlan_pkt = dpkt.ieee80211.IEEE80211(buf[RT_HDR_LEN:])
    ftype = ieee80211_ftype(wlan_pkt.type)
    stype = ieee80211_stype(wlan_pkt.subtype)

    if rt.rate_present:
        # rates are in 500kbps increments.
        rate = int(rt.rate.val)/2
    else:
        # set rate to the lowest n rate when we don't know what it is.
        rate = 65
    if rt.flags_present:
        flags = rt.flags.val
    else:
        flags = 0 
    #if wlan_pkt.type == IEEE80211_FTYPE_DATA:
        #print "packet is not data %d" % (wlan_pkt.type)
    #    continue
    duration = ieee80211_frame_duration(flags & PHY_FLAG_MODE_MASK, buf_len,
                             rate, flags & PHY_FLAG_SHORTPRE,
                             0, wlan_pkt.type,wlan_pkt.subtype, 0,wlan_pkt.retry)
    durs.append(duration)
    print "%f,%d,%s,%s" % (ts, duration, ftype, stype)     

f.close()                    
