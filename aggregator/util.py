import binascii
import dpkt
import sys
from socket import ntohs
from subprocess import *
import string

import socket
import fcntl
import struct
import dpkt

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])


def get_mac_address(intf):
    cmd = "ifconfig %s" % intf
    pipe = Popen(cmd,shell=True,stdout=PIPE)
    out,err = pipe.communicate()
    if (err):
        print "ifconfig failed - exiting...(%s)" % err
        sys.exit(0)
    else:
        line = string.split(out,"\n")[0]
        mac_addr = string.split(line.rstrip()," ")[-1]
        return mac_addr

def is_ack(pkt):
    return pkt.type == 1 and pkt.subtype == 13	#ACK

def is_blockack(pkt):
    return pkt.type == 1 and pkt.subtype == 9	#BLOCKACK

#def is_ack_to_ap(ackdst, ap_hw_ids):
#    return ackdst in ap_hw_ids

def is_from_ap(pkt):
    return is_beacon(pkt) or pkt.from_ds or is_probe_response(pkt)

def is_to_ap(pkt):
    return pkt.to_ds or is_probe_request(pkt)

def is_beacon(ieee):
    return (ieee.type == 0 and ieee.subtype == 0x08)

def is_probe_response(ieee):
    return (ieee.type == 0 and ieee.subtype == 0x05)

def is_probe_request(ieee):
    return (ieee.type == 0 and ieee.subtype == 0x04)

def has_src_dst(ieee):
    return (ieee.type == 0 or ieee.type == 2)

def has_bad_fcs(rdtap):
    return (rdtap.flags_present and rdtap.flags.val & 0x50 == 0x50)

def get_channel(pkt):
    rdtap = dpkt.radiotap.Radiotap(pkt)
    if has_bad_fcs(rdtap):
        return None
    elif rdtap.channel_present:
        return ntohs(rdtap.channel.freq)
    else:
        return None

def get_rdtap_from_pkt(pkt):
    return dpkt.radiotap.Radiotap(pkt)

def get_rdtap_len(rdtap):
    return rdtap.length >> 8

def get_ieee_from_pkt(pkt):
    ie = None
    rdtap = dpkt.radiotap.Radiotap(pkt)
    if has_bad_fcs(rdtap):
    	#print 'get_ieee_from_pkt:bad_fcs'
        return None
    else:
        rd_len = rdtap.length >> 8
	with_fcs = True
        try:
            ie = dpkt.ieee80211.IEEE80211(pkt[rd_len:-4])	#assuming fcs
            #return ie
        except Exception as e:
	    #print e
    	    #print 'get_ieee_from_pkt:exception'
            #return None
	    with_fcs = False

	if ie == None:
	  try:
	      ie = dpkt.ieee80211.IEEE80211(pkt[rd_len:])		#assuming no fcs
	      #return ie
	  except Exception as e:
	      #print e
	      #print 'get_ieee_from_pkt:exception'
	      return None

	if is_blockack(ie):
	  class MyBLOCKACK(dpkt.Packet):
	    __hdr__ = (
		('dst', '6s', '\x00' * 6),
		('src', '6s', '\x00' * 6),
		)
	  #print 'setting ie.myblockack'
	  ie.myblockack = MyBLOCKACK(pkt[rd_len+ie.__hdr_len__:])
	  #ie.myblockack = MyBLOCKACK(pkt[rd_len+4:])

	return ie


def get_link(pkt):
    ap=client=dst=src=None
    if (pkt.type == 0):
        ap = binascii.hexlify(pkt.mgmt.bssid)
        if is_from_ap(pkt):
            client = binascii.hexlify(pkt.mgmt.dst)
            dst = client
            src = ap
        elif is_to_ap(pkt):
            client = binascii.hexlify(pkt.mgmt.src)
            src = client
            dst = ap
    #elif (pkt.type == 1 and pkt.subtype == 13):	#ACK
    elif is_ack(pkt): 
	ack_dst = binascii.hexlify(pkt.ack.dst)

    elif is_blockack(pkt):
	ack_dst = binascii.hexlify(pkt.myblockack.dst)
	ack_src = binascii.hexlify(pkt.myblockack.src)
	#print 'blockack:', ack_dst, ack_src

    elif (pkt.type == 2 and (pkt.subtype == 0 or pkt.subtype == 4 or pkt.subtype == 8)):
        #interDS data.
        if (pkt.to_ds and pkt.from_ds):
            ap = binascii.hexlify(pkt.data_frame.src)
        else:
            ap = binascii.hexlify(pkt.data_frame.bssid)
        if is_from_ap(pkt):
            client = binascii.hexlify(pkt.data_frame.dst)
        elif is_to_ap(pkt):
            client = binascii.hexlify(pkt.data_frame.src)
    bssid = ap
    if pkt.from_ds:
        src = ap
        dst = client
    else:
        src = client
        dst = ap

    #if (pkt.type == 1 and pkt.subtype == 13):	#ACK
    if is_ack(pkt):  
      dst = ack_dst

    if is_blockack(pkt):
      dst = ack_dst
      src = ack_src

    return ap,client,src,dst,bssid

def get_packet_duration(packet):
    rdtap = dpkt.radiotap.Radiotap(packet)
    rd_len = rdtap.length >> 8
    length = len(packet) - rd_len
    if (get_rate(rdtap) > 0):
        duration = float(8*(length+4))/float(rdtap.rate.val/2)
    else:
        return 0
    if (rdtap.flags_present and rdtap.flags.val & 0x02):
        #short preamble
        duration += 96
    else:
        duration += 192
    return duration

def get_rate(rdtap):
    if not rdtap.rate_present or rdtap.rate.val == 0:
        return -1
    else:
        return rdtap.rate.val/2
    

def process_packet(timestamp, packet, total_duration, rates_duration, hosts_duration, packet_stats):

    src=dst=rate=duration=None
    packet_stats['captured'] += 1


    rdtap = dpkt.radiotap.Radiotap(packet)
    if has_bad_fcs(rdtap):
        packet_stats['bad_fcs'] += 1
        return -1


    # radiotap's length is not converted properly...
    rd_len = rdtap.length >> 8
    try:
        ie = dpkt.ieee80211.IEEE80211(packet[rd_len:-4])
    except dpkt.NeedData:
        print "packet cannot be decoded - skipping..."
        return -1

    length = len(packet) - rd_len
    if not rdtap.rate_present or rdtap.rate.val == 0:
        return -1
    
    duration = float(8*(length+ 4))/float(rdtap.rate.val/2)
    if (rdtap.flags_present and rdtap.flags.val & 0x02):
        #short preamble
        duration += 96
    else:
        duration += 192

    if (ie.type == 0):
        src = binascii.hexlify(ie.mgmt.src)
        dst = binascii.hexlify(ie.mgmt.dst)
    elif (ie.type == 2 and ie.subtype == 0):
        src = binascii.hexlify(ie.data_frame.src)
        dst = binascii.hexlify(ie.data_frame.dst)
    
    rate = rdtap.rate.val/2

    total_duration['all'] += duration
    if ie.type == 0:
        total_duration['mgmt'] += duration
    if ie.type == 1:
        total_duration['ctrl'] += duration
    if ie.type == 2:
        total_duration['data'] += duration
    if is_beacon(ie):
        total_duration['beacon'] += duration

    if rate:
        if not rates_duration.has_key(str(rate)):
            rates_duration[str(rate)] = 0

        rates_duration[str(rate)] += duration
    if src:
        if not hosts_duration.has_key(src):
            hosts_duration[src] = 0
        if not hosts_duration.has_key(dst):
            hosts_duration[dst] = 0
        hosts_duration[src] += duration
        hosts_duration[dst] += duration
 

    if (src and dst):
        try:
            links_duration[str((src,dst))]['dur'] += duration
            packet_stats['decoded'] += 1
        except KeyError:
            if (src and dst):
                links_duration[str((src,dst))]  = {'dur':duration,'src':src,'dst':dst}
                packet_stats['decoded'] += 1
            else:
                return -1
    return 0

def virt_to_phy(node):
    if node == None:
        return None
    else:
        _node = "%02x%s" % ((int(node[0:2],16) & int('fc',16)),node[2:])
        return _node
