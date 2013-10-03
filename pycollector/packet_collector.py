#!/usr/bin/env python

import zmq
import random
import sys
import time
import pcap
import dpkt
import sys
import binascii
from optparse import OptionParser
import pymongo
from subprocess import *
import string
import pprint
import pickle


port = "5556"

if __name__=="__main__":
    parser = OptionParser()
    parser.add_option("-i","--intf",dest="intf",
                      default="wlan0",
                      help="Interface or file to read from")
    parser.add_option("-s","--server",dest="server",
                      default="localhost",
                      help="hostname for the MongoDB server")
    parser.add_option("-p","--port",dest="port",
                      type="int", default=27017,
                      help="port for the MongoDB server")
    parser.add_option("-m","--mongo",dest="mongo",
                      action="store_true", default=False,
                      help="If set, send logs to a MongoDB server.")
    parser.add_option("-l","--loop",dest="loop",
                      action="store_true", default=False,
                      help="If set, loop monitoring between channels 1,6,11.")
    parser.add_option("-v","--verbose",dest="verbose",
                      action="store_true", default=False,
                      help="verbose output.")

    (options, args) = parser.parse_args()


    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://127.0.0.1:%s" % port)

    p = pcap.pcap(options.intf)
    while True:
        try:
            ts, pkt = p.next()
        except StopIteration:
            print "pcap file ended..."
            break
        topic = 'packet-in'
        socket.send(topic, zmq.SNDMORE)
        socket.send_json({"ts":ts}, zmq.SNDMORE)
        socket.send(pkt)
