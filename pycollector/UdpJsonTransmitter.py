#!/usr/bin/env python
import threading
import sys
import time
import socket
import json
#from util_ap import get_ip_address
from util_ap import get_mac_address

MESSAGE = "Hello, World!"

class UdpJsonTransmitter(threading.Thread):
    def __init__(self, intf='wlan0', port=5590, id='deadbeef', filter=''):
        threading.Thread.__init__(self)
        self.intf = intf
        self.socket = None
        self.port = port
        self.id = id
	self.filter = filter
	#self.bpf = pcapy.compile(127, 1500, self.filter, 0, 1)
    
    def run(self):
	sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP

        #print "opening %s" % self.intf
        #p = pcap.pcap(self.intf)
	#p.setfilter(self.filter)
        while True:
            try:
                ts,pkt = p.next()
            except StopIteration:
                print "pcap file ended..."
                break
	    pkt_content = pkt[0:min(len(pkt),800)]
	    ser = json.dumps({"ts":ts, 'id':self.id, 'len':len(pkt)})
	    json_len_s = '%04d' % len(ser)
	    dgram = json_len_s + ser + pkt_content
            sock.sendto(dgram, (UDP_IP, UDP_PORT))

            time.sleep(0.0005)


def main():
    print "UDP target IP:", UDP_IP
    print "UDP target port:", UDP_PORT
    #print "message:", MESSAGE

    
    #ID = get_ip_address(UPWARD_PORT)
    ID = get_mac_address(UPWARD_PORT)
    udpJsonTransmitter = UdpJsonTransmitter(intf=INTF,filter=FILTER, id=ID)

    udpJsonTransmitter.setDaemon(True)
    udpJsonTransmitter.start()

    #TODO : stop the threads using ctrl-c
    while(True):
        time.sleep(60)


if __name__ == "__main__":
  main()




