#!/usr/bin/env python
import pcap
#import pcapy
import threading
import sys
import time
from conf import *
import socket
import json
#from util_ap import get_ip_address
from util_ap import get_mac_address

MESSAGE = "Hello, World!"

FILTER = DEF_COL_FILTER

if len(sys.argv) > 1:
    POLL_INTERVAL = int(sys.argv[1])

if len(sys.argv) > 2:
    INTF = sys.argv[2]

if len(sys.argv) > 3:
    FILTER += ' and (' + ' '.join(sys.argv[3:]) + ')'

#the pypcap version (not pylibpcap version)
class Collector(threading.Thread):
    '''Collects packets'''
    def __init__(self, intf='wlan0', port=5556, id='deadbeef', filter=''):
        threading.Thread.__init__(self)
        self.intf = intf
        self.socket = None
        self.port = port
        self.id = id
	self.filter = filter
	#self.bpf = pcapy.compile(127, 1500, self.filter, 0, 1)
    
    def run(self):
        #context = zmq.Context()
        #socket = context.socket(zmq.PUB)
	#socket.setsockopt(zmq.HWM, 1000)	#to limit message queue length (and memory)
        #socket.connect("tcp://thetida.stanford.edu:%d" % PROXY_PUBLISHER)

	sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP

        print "opening %s" % self.intf
        p = pcap.pcap(self.intf)
	p.setfilter(self.filter)
        while True:
            try:
                ts,pkt = p.next()
            except StopIteration:
                print "pcap file ended..."
                break
            #topic = 'packet-in'
            #socket.send(topic,zmq.SNDMORE)
            #socket.send_json({"ts":ts, 'id':self.id, 'len':len(pkt)},zmq.SNDMORE)
            #socket.send(pkt[0:min(len(pkt),2300)])

	    #sock.sendto(json.dumps(MESSAGE), (UDP_IP, UDP_PORT))
            #sock.sendto(json.dumps({"ts":ts, 'id':self.id, 'len':len(pkt)}), (UDP_IP, UDP_PORT))
            #sock.sendto(json.dumps({"ts":ts, 'id':self.id, 'len':len(pkt),'pkt':MESSAGE}), (UDP_IP, UDP_PORT))
	    #pkt_content = pkt[0:min(len(pkt),2300)]
	    pkt_content = pkt[0:min(len(pkt),800)]
	    ser = json.dumps({"ts":ts, 'id':self.id, 'len':len(pkt)})
	    #ser = json.dumps({"ts":ts, 'id':self.id, 'len':len(pkt),'pkt':pkt_content})
	    #print ser
	    #print '%04d' % len(ser)
	    json_len_s = '%04d' % len(ser)
	    #print type(json_len_s), type(ser), type(pkt_content)
	    dgram = json_len_s + ser + pkt_content
            sock.sendto(dgram, (UDP_IP, UDP_PORT))

	    #raw_input()
            time.sleep(0.0005)


def main():
    print "UDP target IP:", UDP_IP
    print "UDP target port:", UDP_PORT
    #print "message:", MESSAGE

    
    #ID = get_ip_address(UPWARD_PORT)
    ID = get_mac_address(UPWARD_PORT)
    collector = Collector(intf=INTF,filter=FILTER, id=ID)

    collector.setDaemon(True)
    collector.start()

    #TODO : stop the threads using ctrl-c
    while(True):
        time.sleep(60)


if __name__ == "__main__":
  main()




