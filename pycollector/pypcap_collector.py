#!/usr/bin/env python
import pcap
import threading
import zmq
import sys
import time
from conf import *

if len(sys.argv) > 1:
    POLL_INTERVAL = int(sys.argv[1])

if len(sys.argv) > 2:
    INTF = sys.argv[2]

#the pypcap version (not pylibpcap version)
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
        socket = context.socket(zmq.PUB)
	socket.setsockopt(zmq.HWM, 1000)	#to limit message queue length (and memory)
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

def main():
    collector = Collector(intf=INTF)

    collector.setDaemon(True)
    collector.start()

    #TODO : stop the threads using ctrl-c
    while(True):
        time.sleep(60)


if __name__ == "__main__":
  main()
