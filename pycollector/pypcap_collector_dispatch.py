#!/usr/bin/env python
#import aggregators
import time
import sys
import threading
import zmq
import pcap
import pcapy
from conf import *

if len(sys.argv) > 1:
    POLL_INTERVAL = int(sys.argv[1])

if len(sys.argv) > 2:
    INTF = sys.argv[2]

collector = None

#def pkt_handler(pkt_len, data, ts):
def pkt_handler(ts, pkt, args=None):
    topic = 'packet-in'
    collector.socket.send(topic,zmq.SNDMORE)
    collector.socket.send_json({"ts":ts, 'id':collector.id, 'len':len(pkt)},zmq.SNDMORE)
    collector.socket.send(pkt[0:min(len(pkt),2300)])

class Collector(threading.Thread):
    '''Collects packets'''
    def __init__(self, intf='wlan0', port=5556, id='deadbeef'):
        threading.Thread.__init__(self)
        self.intf = intf
        self.socket = None
        self.port = port
        self.id = id
    
    def run_old(self):
        context = zmq.Context()
        socket = context.socket(zmq.PUB)
        socket.connect("tcp://thetida.stanford.edu:%d" % PROXY_PUBLISHER)
        print "opening %s" % self.intf
        p = pcap.pcap(self.intf)
        while True:
            try:
                ts,pkt = p.next()
            except StopIteration:
                print "pcap file ended..."
                break
            topic = 'packet-in'
            socket.send(topic,zmq.SNDMORE)
            socket.send_json({"ts":ts, 'id':self.id, 'len':len(pkt)},zmq.SNDMORE)
            socket.send(pkt[0:min(len(pkt),2300)])
#            time.sleep(0.0005)

    def run(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.PUB)
	self.socket.setsockopt(zmq.HWM, 1000)	#to limit message queue length (and memory)
        self.socket.connect("tcp://thetida.stanford.edu:%d" % PROXY_PUBLISHER)
        print "opening %s" % self.intf
        p = pcap.pcap(self.intf)
        while True:
            try:
                #ts,pkt = p.next()
		p.dispatch(1, pkt_handler)
            except StopIteration:
                print "pcap file ended..."
                break

def main():
    global collector
    #collector = aggregators.Collector(intf=INTF)

    collector = Collector(intf=INTF)

    collector.setDaemon(True)
    collector.start()

    #TODO : stop the threads using ctrl-c
    while(True):
        time.sleep(60)


if __name__ == "__main__":
  main()
