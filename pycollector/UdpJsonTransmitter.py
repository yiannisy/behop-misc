#!/usr/bin/env python
import threading
import sys
import time
import socket
import json
#from util_ap import get_ip_address
from util_ap import get_mac_address

#for testing
from GenericSampler import *

MESSAGE = "Hello, World!"

class UdpJsonTransmitter(threading.Thread):
    def __init__(self, sampler, dst_ip, dst_port, interval=5, id='deadbeef', filter=''):
        threading.Thread.__init__(self)
	self.sampler = sampler
        self.dst_port = dst_port
	self.dst_ip = dst_ip
	self.interval = interval
        self.id = id
	self.filter = filter

        self.socket = None

	print "UDP target IP:", self.dst_ip
	print "UDP target port:", self.dst_port
    
    def run(self):
	sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP

        while True:
            try:
	      ts = time.time()
	      sample = self.sampler.next()
	      print sample
            except:
                print "UdpJsonTransmitter could not get sample, continuing..."
	        time.sleep(self.interval)
                continue

	    ser = json.dumps({"ts":ts, 'id':self.id, 'sample':sample})
	    dgram = ser

            sock.sendto(dgram, (self.dst_ip, self.dst_port))

            time.sleep(self.interval)


def main():
    UPWARD_PORT = 'br0'
    DST_IP = "172.24.74.179"
    DST_PORT = 5590

    sampler = TestSampler()

    
    #ID = get_ip_address(UPWARD_PORT)
    ID = get_mac_address(UPWARD_PORT)
    udpJsonTransmitter = UdpJsonTransmitter(sampler, DST_IP, DST_PORT, 1, ID)

    udpJsonTransmitter.setDaemon(True)
    udpJsonTransmitter.start()

    #TODO : stop the threads using ctrl-c
    while(True):
        time.sleep(60)


if __name__ == "__main__":
  main()




