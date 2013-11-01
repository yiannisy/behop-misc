#!/usr/bin/env python
import threading
import zmq
import sys
import time
import string
import util
import pcap
import pcapy
import os, signal
import pickle
from util import virt_to_phy
import random
import socket
import collections
from infobases import PiInfoBase
from conf import *
import json
from ap_hw_ids import *
import struct



class Proxy(threading.Thread):
    def __init_(self):
        pass
    def run(self):
        try:
            self.context = zmq.Context(1)
            frontend = self.context.socket(zmq.SUB)
            frontend.bind("tcp://*:%d" % PROXY_PUBLISHER)
            frontend.setsockopt(zmq.SUBSCRIBE,"")
            
            backend = self.context.socket(zmq.PUB)
            backend.bind("tcp://*:%d" % PROXY_SUBSCRIBER)
            
            zmq.device(zmq.FORWARDER, frontend, backend)
        except Exception,e:
            print e
        finally:
            pass
            #pass
            #frontend.close()
            #backend.close()
            #self.context.term()



class Aggregator(threading.Thread):
    '''An aggregator subscribes to a set of topics.'''
    def __init__(self, feeds=None):
        '''feeds is a list of tuples with publisher + topic information.'''
        threading.Thread.__init__(self)
        self.feeds = feeds
        self.socket = None
        self.running = True
        self.subscribe()
	self.infoBase = None

    def subscribe(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        for feed in self.feeds:
            self.socket.connect(feed[0])
            self.socket.setsockopt(zmq.SUBSCRIBE, feed[1])

    def set_info_base(self, ib):
      self.infoBase = ib

    def get_info_base(self):
      return self.infoBase

    def query(self, q):
      return self.infoBase.query(q)

    def stop(self):
        self.running = False
            
    def run(self):
        pass

class UdpAggregator(Aggregator):
  '''A UDP aggregator to receive trace information from AP collectors'''
  def subscribe(self):
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.socket.bind((self.IP, self.PORT))

class LinkAggregator(Aggregator):
    def __init__(self, url, interval=10):
        """
        @url: the url of the publisher
        @interval: how often to export a summary
        """
        feeds = [(url,'packet-in')]
        Aggregator.__init__(self, feeds)
        self.interval = interval
        self.pubsocket = self.context.socket(zmq.PUB)
        self.pubsocket.bind("tcp://127.0.0.1:5557")
        self.pubtopic = 'num_links'

    def run(self):
        print "waiting for events..."
        links = {}
        last_ts = 0
        while(self.running):
            topic = self.socket.recv()
            ts = self.socket.recv_json()['ts']
            if last_ts == 0:
                last_ts = ts
            pkt = self.socket.recv()
            ap, client, src,dst = util.get_link(pkt)
            links[(src,dst)] = 1
            if ts - last_ts > self.interval:
                self.pubsocket.send(self.pubtopic, zmq.SNDMORE)
                self.pubsocket.send(str(len(links.keys())))
                print links.keys()
                links = {}
                last_ts = ts

class NodeAggregator(Aggregator):
    def __init__(self, url, interval=10, filter=''):
        """
        @url: the url of the publisher
        @interval: how often to export a summary
        """
        feeds = [(url,'packet-in')]
        Aggregator.__init__(self, feeds)
        self.stats = []
        self.url = url
        self.interval = interval
        self.pubsocket = self.context.socket(zmq.PUB)
        self.pubsocket.bind("tcp://127.0.0.1:5558")
        self.pubtopic = 'num_nodes'
        self.filter = filter
        self.bpf = pcapy.compile(127, 1500, self.filter, 0, 1)


    def stop(self):
        f = open('nodeagg-%s-%s.txt' % (self.url[6:-5],self.filter),'w')
        pickle.dump(self.stats,f)
        f.close()
        Aggregator.stop(self)

    def run(self):
        print "waiting for events..."
        srcs = {}
        dsts = {}
        nodes = {}
        last_ts = 0
        while(self.running):
            topic = self.socket.recv()
            ts = self.socket.recv_json()['ts']
            if last_ts == 0:
                last_ts = ts
            packet = self.socket.recv()
            if not self.bpf.filter(packet):
                continue
            rdtap = util.get_rdtap_from_pkt(packet)
            if util.has_bad_fcs(rdtap):                
                continue
            pkt = util.get_ieee_from_pkt(packet)
            if pkt == None:
                print "cannot decode packet - skipping..."
                continue

            ap, client, src,dst = util.get_link(pkt)
            duration = util.get_packet_duration(packet)
            if not nodes.has_key(src):
                nodes[src] = 0
            if not nodes.has_key(dst):
                nodes[dst] = 0
            if not srcs.has_key(src):
                srcs[src] = 0
            if not dsts.has_key(dst):
                dsts[dst] = 0


            nodes[src] += duration
            nodes[dst] += duration
            srcs[src] += duration
            dsts[dst] += duration
            if ts - last_ts > self.interval:
                #stats = {"srcs":len(srcs.keys()), "dsts":len(dsts.keys()), "nodes":len(nodes.keys())}
                #print stats
                print last_ts,srcs
                self.stats.append((last_ts,srcs))
                self.pubsocket.send(self.pubtopic, zmq.SNDMORE)
                self.pubsocket.send(str(self.stats))
                srcs = {}
                dsts = {}
                nodes = {}
                last_ts = ts

class ApAggregator(Aggregator):
    def __init__(self, url, interval=10):
        """
        @url: the url of the publisher
        @interval: how often to export a summary
        """
        feeds = [(url,'packet-in')]
        Aggregator.__init__(self, feeds)
        self.interval = interval
        self.pubsocket = self.context.socket(zmq.PUB)
        self.pubsocket.bind("tcp://127.0.0.1:5559")
        self.pubtopic = 'num_aps'

    def run(self):
        print "waiting for events..."
        aps = {}
        last_ts = 0
        while(self.running):
            topic = self.socket.recv()
            ts = self.socket.recv_json()['ts']
            if last_ts == 0:
                last_ts = ts
            pkt = self.socket.recv()
            if util.is_from_ap(pkt):
                ap, client, src,dst = util.get_link(pkt)
                aps[src] = 1
            
            if ts - last_ts > self.interval:
                print "%f : # of aps : %d" % (ts, len(aps.keys()))
                print sorted(aps.keys())
                self.pubsocket.send(self.pubtopic, zmq.SNDMORE)
                self.pubsocket.send(str(len(aps.keys())))
                aps = {}
                last_ts = ts
        
class UtilityAggregator(Aggregator):
    def __init__(self, url, interval=1, pub=False, filter=''):
        """
        @url: the url of the publisher
        @interval: how often to export a summary
        """
        feeds = [(url, 'packet-in')]
        Aggregator.__init__(self, feeds)
        self.interval = interval
        self.is_pub = pub
        self.url = url
        self.filter = filter
        self.bpf = pcapy.compile(127, 1500, self.filter, 0, 1)
        self.f = open('%s-%s.txt' % (url[6:-5],filter),'w')
        self.f.write('url,filter,ts,kbps,kbpvs,kbpvrs,pkts,ma_pkt,usecs\n')
               
    def run(self):
        last_ts = 0
        bits = 0
        rbits = 0
        pkts = 0
        duration = 0
        snrs = []
        max_size_pkt = 0
        while(self.running):
            topic = self.socket.recv()
            ts = self.socket.recv_json()['ts']
            if last_ts == 0:
                last_ts = ts
            packet = self.socket.recv()
            #print "packet size %d" % len(packet)
            if not self.bpf.filter(packet):
                continue
            rdtap = util.get_rdtap_from_pkt(packet)
            pkt_len = len(packet) - util.get_rdtap_len(rdtap)
            bits += pkt_len*8
            pkts += 1
            duration += util.get_packet_duration(packet)
            rbits += util.get_rate(rdtap)*util.get_packet_duration(packet)
            if (pkt_len*8  > util.get_rate(rdtap)*util.get_packet_duration(packet)):
                print "bpvs > bpvrs (%d, %d)" % (pkt_len*8, util.get_rate(rdtap)*util.get_packet_duration(packet))
            if pkt_len > max_size_pkt:
                max_size_pkt = pkt_len
            
            if ts - last_ts > self.interval:
                print "%s : %s : %f : %fkbps, %fkbpvs, %fkbpvrs, %d pkts, %d max_pkt, %f usecs" % (self.url, self.filter, ts, 
                                                                             bits/(1e3*(ts-last_ts)), 
                                                                             bits/(1e-3*(duration)),
                                                                             rbits/(1e-3*(duration)),
                                                                             pkts, max_size_pkt, duration)
                self.f.write("%s,%s,%f,%f,%f,%f,%d,%d,%f\n" % (self.url, self.filter, ts, 
                                                                                                          bits/(1e3*(ts-last_ts)), 
                                                                                                          bits/(1e-3*(duration)),
                                                                                                          rbits/(1e-3*(duration)),
                                                                                                          pkts, max_size_pkt, duration))

                bits = 0
                rbits = 0
                pkts = 0
                last_ts = ts
                #snrs = []
                duration = 0
                max_size_pkt = 0
        self.f.close()

class SnrAggregator(Aggregator):
    def __init__(self, url, interval=1, pub=False, filter='type data'):
        """
        @url: the url of the publisher
        @interval: how often to export a summary
        """
        feeds = [(url, 'packet-in')]
        Aggregator.__init__(self, feeds)
        self.interval = interval
        self.is_pub = pub
        self.url = url
        self.filter = filter
        self.bpf = pcapy.compile(127, 1500, self.filter, 0, 1)
        self.snrs = {}
        self.f = open('snr-%s-%s.txt' % (url[6:-5],filter),'w')
        self.f.write('url,filter,ts,kbps,kbpvs,kbpvrs,pkts,ma_pkt,usecs\n')
               
    def run(self):
        last_ts = 0
        bits = 0
        rbits = 0
        pkts = 0
        duration = 0
        max_size_pkt = 0
        while(self.running):
            topic = self.socket.recv()
            meta = self.socket.recv_json()
            ts = meta['ts']
            id = meta['id']            
            if last_ts == 0:
                last_ts = ts
            packet = self.socket.recv()
            #print "packet size %d" % len(packet)
            if not self.bpf.filter(packet):
                continue
            rdtap = util.get_rdtap_from_pkt(packet)
            ieee_pkt = util.get_ieee_from_pkt(packet)
            if rdtap == None or ieee_pkt == None:
                print "cannot decode rdtap/ieee --- continue..."
                continue
            ap,client,src,dst = util.get_link(ieee_pkt)
            src = virt_to_phy(src)
            if rdtap.ant_sig_present:
                snr = rdtap.ant_sig.db - (-90)
            else:
                snr = 0
            seq = socket.ntohs(ieee_pkt.data_frame.frag_seq)
            try:
                self.snrs[(src,id)].append((ts,seq,snr))
            except KeyError:
                self.snrs[(src,id)] = [(ts,seq,snr)]
            pkts += 1
            
            if ts - last_ts > self.interval and pkts > 0:
                self.detect_weak_nodes()
                self.snrs = {}
                last_ts = ts

            
        self.f.close()
        
    def detect_weak_nodes(self):
        unique_nodes = set([link[0] for link in self.snrs.keys()])
        print "\n\n%d lins sniffed" % len(self.snrs.keys())
        print "%d unique nodes" % len(unique_nodes)
        weak_nodes = []
        for node in unique_nodes:
            links = [link for link in self.snrs.keys() if link[0] == node]
            node_avg_snr = []
            for link in links:
                snrs = [x[2] for x in self.snrs[link]]
                seqs = [x[1] for x in self.snrs[link]]
                avg_snr = sum(snrs)/len(snrs)
                duplicates = len(seqs) - len(set(seqs))
                pkts = len(set(seqs))
                node_avg_snr.append(avg_snr)
            if max(node_avg_snr) < SNR_ALERT_THRESHOLD:
                weak_nodes.append(node)
                print node, node_avg_snr
                #print zip(links,node_avg_snr)
                #print "link : %s, avg-snr:%f, duplicates:%d, # of packets: %d, uniq/dup ratio : %f" % (
                #                                                                                       link, avg_snr, len(seqs) - len(set(seqs)),
                 #                                                                                      len(snrs),float(duplicates)/pkts)



class HostAggregator(Aggregator):
    def __init__(self, url, interval=1, host=None, pub=False):
        """
        @url: the url of the publisher
        @interval: how often to export a summary
        """
        feeds = [(url,'packet-in')]
        Aggregator.__init__(self, feeds)
        self.interval = interval
        self.is_pub = pub
        self.url = url
        self.host = host
        if self.is_pub == True:
            pass

    def run(self):
        last_ts = 0
        snrs = []
        pkts = 0
        bits = 0
        while(self.running):
            topic = self.socket.recv()
            ts = self.socket.recv_json()['ts']
            if last_ts == 0:
                last_ts = ts
            packet = self.socket.recv()
            rdtap = util.get_rdtap_from_pkt(packet)
            if util.has_bad_fcs(rdtap):                
                continue
            #channel = util.get_channel(packet)
            # freq -> channel for 802.11g
            #channel = 1 + (int(channel) - 2412)/5
            pkt = util.get_ieee_from_pkt(packet)
            if pkt == None:
                print "cannot decode packet - skipping..."
                continue
            ap, client, src, dst = util.get_link(pkt)
            if (ap == self.host) or (client == self.host):
                pkts += 1
                bits += 1
                #snrs.append(rdtap.ant_sig.db - (-90))
                duration =+ util.get_packet_duration(packet)
            #else:
            #    print self.host, ap, client
            
            if ts - last_ts > self.interval and pkts > 0:
                print "%f : %s : %s : %fkbps, %d pkts, %d dB SNR" % (ts, self.url, self.host, 
                                                                  bits/(1e3*(ts-last_ts)),
                                                                  pkts, sum(snrs)/len(snrs))
                bits = 0
                pkts = 0
                snrs = []
                last_ts = ts



class HomeAggregator(Aggregator):
    def __init__(self, url, interval=10, filter='', duration=0, pub=False):
        """
        @url: the url of the publisher
        @interval: how often to export a summary
        """
        feeds = [(url,'packet-in')]
        Aggregator.__init__(self, feeds)
        self.interval = interval
        self.is_pub = pub
        self.url = url
        self.duration = 0
        self.filter = filter
        self.bpf = pcapy.compile(127, 1500, self.filter, 0, 1)
        if self.is_pub == True:
            self.pubsocket = self.context.socket(zmq.PUB)
            self.pubsocket.bind("tcp://127.0.0.1:5560")
            self.pubtopic = 'homes'

    def stop(self):
        f = open('homeagg-%s-%s.txt' % (self.url[6:-5],self.filter),'w')
        pickle.dump([self.homes,self.phy_aps],f)
        f.close()
        Aggregator.stop(self)
             
    def run(self):
        print "waiting for events..."
        self.homes = {}
        self.phy_aps = {}
        last_ts = 0
        while(self.running):
            topic = self.socket.recv()
            ts = self.socket.recv_json()['ts']
            if last_ts == 0:
                last_ts = ts
            packet = self.socket.recv()
            if not self.bpf.filter(packet):
                continue
            rdtap = util.get_rdtap_from_pkt(packet)
            if util.has_bad_fcs(rdtap):                
                continue
            channel = util.get_channel(packet)
            if channel:
                # freq -> channel for 802.11g
                channel = 1 + (int(channel) - 2412)/5
            
            pkt = util.get_ieee_from_pkt(packet)
            if pkt == None:
                print "cannot decode packet - skipping..."
                continue
            ap, client, src, dst = util.get_link(pkt)
            if ap == None or client == None:
                #print "ap|client is none (%s,%s, %x%x)" % (ap,client, pkt.type, pkt.subtype)
                continue
            if ap not in self.homes.keys():
                self.homes[ap] = {'clients':{}, 'channel':channel}
            self.homes[ap]['clients'][client] = 1
            phy_ap = virt_to_phy(ap)
            self.phy_aps[phy_ap] = 1            
            
            if ts - last_ts > self.interval:
                print "%f : %s : # of homes : %d ( phy : %d)" % (ts, self.url, len(self.homes.keys()), 
                                                                 len(self.phy_aps.keys()))
                #for home in sorted(homes.keys()):
                    #print "%s : %d %d (%s)" % (home,len(homes[home]['clients'].keys()),
                    #                        homes[home]['channel'], 
                    #                        homes[home]['clients'].keys())
                if self.is_pub:
                    self.pubsocket.send(self.pubtopic, zmq.SNDMORE)
                    self.pubsocket.send(str(homes))
                #homes = {}
                #phy_aps = {}
                    
                last_ts = ts



class PiAggregator(Aggregator):
    def __init__(self, url, interval=1, pub=False, filter='', MAXLEN=1000):
        """
        @url: the url of the publisher
        @interval: how often to export a summary
        """
        feeds = [(url, 'packet-in')]
        Aggregator.__init__(self, feeds)
        self.interval = interval
        self.is_pub = pub
        self.url = url
        self.filter = filter
        self.bpf = pcapy.compile(127, 1500, self.filter, 0, 1)
        self.f = open('%s-%s.txt' % (url[6:-5],filter),'w')
        self.f.write('url,filter,ts,kbps,kbpvs,kbpvrs,pkts,ma_pkt,usecs\n')

	self.db = collections.deque(maxlen=MAXLEN)	#circular buffer of length MAXLEN
	self.set_info_base(PiInfoBase(self))
               
    def run(self):
        last_ts = 0
        bits = 0
        rbits = 0
        pkts = 0
        duration = 0
        snrs = []
        max_pkt_size = 0
        while(self.running):
            topic = self.socket.recv()
            ts = self.socket.recv_json()['ts']
            if last_ts == 0:
                last_ts = ts
            pkt = self.socket.recv()		#to receive pkt data
            #print "pkt size %d" % len(pkt)
            if not self.bpf.filter(pkt):
                continue
            rdtap = util.get_rdtap_from_pkt(pkt)
	    #print 'len of rdtap: %d' % util.get_rdtap_len(rdtap)
            pkt_len = len(pkt) - util.get_rdtap_len(rdtap)
	    max_pkt_size = max(max_pkt_size, pkt_len)
            ieee_pkt = util.get_ieee_from_pkt(pkt)
            if rdtap == None or ieee_pkt == None:
            #if rdtap == None:
                print "cannot decode rdtap/ieee --- continue..."
                continue
            #ap,client,src,dst = util.get_link(ieee_pkt)
            #src = virt_to_phy(src)
            if rdtap.ant_sig_present:
                snr = rdtap.ant_sig.db - (-90)
            else:
                snr = 0
	    snrs.append(snr)

	    link_id = util.get_link(ieee_pkt)
	    ieee_type = ieee_pkt.type
	    ieee_subtype = ieee_pkt.subtype
	    d={'ts':ts,'link_id':link_id,'pkt_len':pkt_len,'snr':snr, 'type':ieee_type, 'subtype':ieee_subtype}
	    #print d
	    #self.db.append({'ts':ts,'link_id':link_id,'pkt_len':pkt_len,'snr':snr})
            
            if ts - last_ts > self.interval:
	      ##print "max_pkt_size: %d, max_snr: %f, min_snr: %f" % (max_pkt_size, max(snrs), min(snrs))
	      max_pkt_size = 0
              snrs = []
        self.f.close()

class PiUdpAggregator(UdpAggregator):
    def __init__(self, TEST_MODE, interval=1, filter=DEF_AGG_FILTER, MAXLEN=10000):
        """
        @interval: how often to export a summary
        """
	self.TEST_MODE = TEST_MODE
	self.IP = UDP_IP
	if TEST_MODE:
	  self.PORT = UDP_PORT_TEST
	else:
	  self.PORT = UDP_PORT_PROD
        UdpAggregator.__init__(self)
        self.interval = interval
        self.filter = filter
        self.bpf = pcapy.compile(127, 1500, self.filter, 0, 1)
        #self.f = open('%s-%s.txt' % (url[6:-5],filter),'w')
        self.f = open('%s-%s.txt' % ("udp",filter),'w')
        self.f.write('url,filter,ts,kbps,kbpvs,kbpvrs,pkts,ma_pkt,usecs\n')

	self.trace = open('piudp-trace.pkl','wb')
	self.resp_log = []

	self.db = collections.deque(maxlen=MAXLEN)	#circular buffer of length MAXLEN
	self.dblock = threading.RLock()

	print 'piudp aggregator receiving on port', self.PORT
	print 'creating pi info base'
	self.set_info_base(PiInfoBase(self))
	print 'created pi info base'

	self.ap_hw_id_list = ap_hw_ids()
               
    def run(self):
        last_ts = 0
        bits = 0
        rbits = 0
        pkts = 0
        duration = 0
        snrs = []
        max_pkt_size = 0
        while(self.running):
	    #resp = self.socket.recv(1024).strip()
	    resp = self.socket.recv(1024).strip()
	    #self.resp_log.append(resp)
	    #if len(self.resp_log) > 2000:
	    #  break

	    if COLLECTOR_MODEL == 'pycollector':
	      #--------------------------
	      # pycollector model
	      #--------------------------
	      json_len_s = str(resp[0:4])
	      json_len = int(json_len_s)

	      #print json_len_s, json_len

	      ser = json.loads(resp[4:(4+json_len)])
	      #print ser

	      pkt_content = resp[(4+json_len):]
	      #print len(pkt_content)

	      ts = ser['ts']
	      ts_rcv = time.time()
	      apid = ser['id']
	      orig_len = ser['len']
	      #-------------------------

	    elif COLLECTOR_MODEL == 'ccollector':
	      #--------------------------
	      # ccollector model
	      #--------------------------
	      json_len_s = resp[0:4]
	      json_len = struct.unpack('i',json_len_s)[0]
	      json_len = socket.ntohl(json_len)
	      #print json_len_s, json_len
	      #print type(json_len_s)

	      ser = json.loads(resp[4:(4+json_len)])
	      #print ser

	      pkt_content = resp[(4+json_len):]
	      #print len(pkt_content)

	      tss = ser['tss']
	      tsu = ser['tsu']
	      ts = tss + 1e-6 * tsu

	      apid = ser['id']
	      intf = ser['mi']		#monitor interface
	      orig_len = ser['len']

	      #print tss, tsu, ts, apid, intf, len(pkt_content)
	      ts_rcv = time.time()
	      #-------------------------
	    else:
	      print 'Bad collector model'
	      sys.exit(0)


            if last_ts == 0:
                last_ts = ts
            #pkt = self.socket.recv()		#to receive pkt data
	    pkt = pkt_content

            #print "pkt size %d" % len(pkt)
            if not self.bpf.filter(pkt):
	    	#print 'no bpf match'
                continue
            rdtap = util.get_rdtap_from_pkt(pkt)
	    #print 'len of rdtap: %d' % util.get_rdtap_len(rdtap)

            ieee_pkt = util.get_ieee_from_pkt(pkt)
            if rdtap == None or ieee_pkt == None:
            #if rdtap == None:
                print "cannot decode rdtap/ieee --- continue..."
                continue
	    #else:
	    #  print 'got ieee_pkt'


            #pkt_len = len(pkt) - util.get_rdtap_len(rdtap)
            pkt_len = orig_len - util.get_rdtap_len(rdtap)
	    max_pkt_size = max(max_pkt_size, pkt_len)

            #ap,client,src,dst = util.get_link(ieee_pkt)
            #src = virt_to_phy(src)
            if rdtap.ant_sig_present:
                snr = rdtap.ant_sig.db - (-90)
            else:
                snr = 0
	    snrs.append(snr)

	    link_id = util.get_link(ieee_pkt) 		#return ap,client,src,dst,bssid for data
							#return sa, src, dst, da, bssid for ack
	    ieee_type = ieee_pkt.type
	    ieee_subtype = ieee_pkt.subtype
	    if ieee_type == 2:			#data
	      seq = socket.ntohs(ieee_pkt.data_frame.frag_seq)
	      ap,client,src,dst,bssid = link_id
	      src_phy = virt_to_phy(src)
	      if util.is_to_ap(ieee_pkt):
		tag = 'DAT_TO_AP'
	      else:
		tag = 'DAT_FR_AP'
	    elif util.is_ack(ieee_pkt):		#ack
	      seq = 0
	      sa, src, dst, da, bssid= link_id 		#return sa, src, dst, da, bssid for ack
	      #if (util.is_ack_to_ap(dst, self.ap_hw_id_list)):
	      #  tag = 'ACK_TO_AP'
	      #else:
	      #  tag = 'ACK_FR_AP'

	      #Explanation: Acks captured on the monitor interface can only be inbound acks
	      #since outbound acks are handled by hardware and don't show up in the sniff;
	      #They may not all be from stations - they could also be from other aps.
	      tag = 'ACK_TO_AP'
	      src_phy = None
	      #print tag,'snr=',snr,'link_id=',link_id
	    elif util.is_blockack(ieee_pkt):	#blockack (11n)
	      #print 'blockack frame type=%s,subtype=%s, continuing...' % (ieee_type, ieee_subtype)
	      ##tag = 'BCK_TO_AP'
	      tag = 'ACK_TO_AP'
	      #print tag,'snr=',snr,'link_id=',link_id
	      src_phy = None
	    else:
	      print 'unhandled frame type=%s,subtype=%s, continuing...' % (ieee_type, ieee_subtype)
	      continue

	    #print 'handled frame type'

	    d={'ts_rcv':ts_rcv,'ts':ts,'apid':apid,'link_id':link_id,'src_phy':src_phy,'seq':seq,'pkt_len':pkt_len,'snr':snr, 'type':ieee_type, 'subtype':ieee_subtype, 'tag':tag}
	    #print tag, d
	    with self.dblock:
	      self.db.append(d)
	    #idx = next(i for i, j in enumerate(self.db) if j['ts_rcv'] > ts_rcv - PIUDP_AGG_WINDOW_LEN_SECS)
	    #print idx, len(self.db)
	    #db_slice = collections.deque(itertools.islice(self.db, idx, len(self.db)))

            
            if ts - last_ts > self.interval:
	      ##print "max_pkt_size: %d, max_snr: %f, min_snr: %f" % (max_pkt_size, max(snrs), min(snrs))
	      max_pkt_size = 0
              snrs = []
        self.f.close()

	pickle.dump(self.resp_log, self.trace)
	self.trace.close()
	print 'dumped self.resp_log'

