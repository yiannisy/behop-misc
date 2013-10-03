#!/usr/bin/env python
import networkx as nx
import zmq
import sys
import string
import util
import pickle
from aggregators import *
import matplotlib
matplotlib.use('Agg')
import pylab
from networkx.readwrite import json_graph
import json

class ServiceStats(Aggregator):
    def __init__(self, url, interval=1, pub=False, filter=''):
        feeds = [(url, 'packet-in')]
        Aggregator.__init__(self, feeds)
        self.g = nx.DiGraph()
        self.interval = interval
        self.is_pub = pub
        self.url = url
        self.filter = filter
        self.bpf = pcapy.compile(127, 1500, self.filter, 0, 1)

	#TODO
        self.snrs = {}
        self.results = []
	self.pkts = []

    def run(self):
        last_ts = 0
        bits = 0
        rbits = 0
        pkts = 0
        duration = 0
        max_size_pkt = 0
        first_ts = time.time()
        while(self.running):
            topic = self.socket.recv()
            meta = self.socket.recv_json()
            ts = meta['ts']
            id = meta['id']            
            id = string.replace(id,'-','')
            id = id[0:12]
            id = string.lower(id)
            if last_ts == 0:
                last_ts = ts
            packet = self.socket.recv()
            #print "packet size %d" % len(packet)
            if not self.bpf.filter(packet):
                continue
            rdtap = util.get_rdtap_from_pkt(packet)
            ieee_pkt = util.get_ieee_from_pkt(packet)
            if rdtap == None or ieee_pkt == None:
                #print "cannot decode rdtap/ieee --- continue..."
                continue
            ap,client,src,dst,bssid = util.get_link(ieee_pkt)
            src = virt_to_phy(src)

	    #TODO
            if rdtap.ant_sig_present:
                snr = rdtap.ant_sig.db - (-90)
            else:
                snr = 0
            #seq = socket.ntohs(ieee_pkt.data_frame.frag_seq)
            seq = 0
            pkts += 1
	    self.pkts.append((ts,ap,client,src,dst,bssid,rdtap,ieee_pkt))

            #try:
            #    self.g[src][id]['snr'].append((ts,seq,snr))
            #    self.g[src][id]['active'] = (id == bssid)
            #except KeyError:                
            #    self.g.add_node(src,bssid=bssid)
            #    self.g.add_node(id,bssid='')
            #    self.g.add_edge(src,id,snr=[(ts,seq,snr)],active=(id==bssid))
            if ts - last_ts > self.interval and pkts > 0:
                print "###################################################"
                print "Packets:"
		list = ["ts: %s  ap: %s  client: %s  src: %s  dst: %s  bssid: %s" % (ts,ap,client,src,dst,bssid) for (ts,ap,client,src,dst,bssid,rdtap,ieee_pkt) in self.pkts]
                print "\n".join(list)
                print "\n"
                print "\n\n"

                #client_nodes = self.get_client_nodes()
                #weak_nodes = self.detect_weak_nodes(-5,25)
                #good_nodes = self.detect_weak_nodes(25,100)
                #ap_nodes = [node for node in self.g.nodes() if self.g.in_degree(node) > 0]
                ##good_nodes = self.detect_connectivity_degree()                
                #neighbors = self.detect_neighbors()
                #self.results.append([self.g.nodes,client_nodes,weak_nodes,good_nodes,neighbors])

                #active_weak_nodes = [node for node in weak_nodes if max([l[1] for l in node[1]]) > 10]
                #active_good_nodes = [node for node in good_nodes if max([l[1] for l in node[1]]) > 10]


                ##print "%d,%d,%d,%d,%d" % (len(self.g.nodes()),len(client_nodes), len(weak_nodes), len(good_nodes), len(neighbors))
                #print "###################################################"
                #print "Weak Nodes"
                #list = ["NODE : %s PKTS : %s SNRs : %s" % (node[0],max([l[1] for l in node[1]]),[l[0] for l in node[1]]) for node in active_weak_nodes]
                #print "\n".join(list)
                #print "\n"
                #print "Good Nodes"
                #list = ["NODE : %s PKTS : %s SNRs : %s" % (node[0],max([l[1] for l in node[1]]),[l[0] for l in node[1]]) for node in active_good_nodes]
                #print "\n".join(list)
                #print "\n\n"

                #self.update_packet_list()
                #self.snrs = {}
                last_ts = ts
		pkts = 0
		self.pkts = []

            if time.time() - first_ts > 10:
                ##nx.write_gpickle(self.g,'graph_pickle_channel11_%d.pkl' % time.time())
                #self.generate_weak_links_map()
                #
                #first_ts = time.time()
                ## f = open('graph-%d.txt' % time.time(),'w')
                ## pickle.dump(self.results,f)
                ## f.close()
                ## self.results = []
                first_ts = time.time()

