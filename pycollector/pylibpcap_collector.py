#!/usr/bin/env python
import pcap
import threading
import sys
import time
import zmq
from conf import *

if len(sys.argv) > 1:
    POLL_INTERVAL = int(sys.argv[1])

if len(sys.argv) > 2:
    INTF = sys.argv[2]

collector = None

def pkt_handler(pkt_len, data, ts):
    topic = 'packet-in'
    collector.socket.send(topic,zmq.SNDMORE)
    collector.socket.send_json({"ts":ts, 'id':collector.id, 'len':pkt_len},zmq.SNDMORE)
    collector.socket.send(data[0:min(pkt_len,2300)])


#the pylibpcap version (not pypcap version)
class Collector(threading.Thread):
    '''Collects packets'''
    def __init__(self, intf='wlan0', port=5556, id='deadbeef'):
        threading.Thread.__init__(self)
        self.intf = intf
        self.socket = None
        self.port = port
        self.id = id
    
    def run(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.PUB)
	self.socket.setsockopt(zmq.HWM, 1000)	#to limit message queue length (and memory)
        self.socket.connect("tcp://thetida.stanford.edu:%d" % PROXY_PUBLISHER)
        print "opening %s" % self.intf
        p = pcap.pcapObject()
	p.open_live(self.intf, 1600, 0, 100)
	try:
	  while True:
	    p.dispatch(1, pkt_handler)
	except StopIteration:
	  print "pcap file ended..."
	  #break
#            time.sleep(0.0005)

def main():
    global collector
    collector = Collector(intf=INTF)

    collector.setDaemon(True)
    collector.start()

    #TODO : stop the threads using ctrl-c
    while(True):
        time.sleep(60)


if __name__ == "__main__":
  main()
