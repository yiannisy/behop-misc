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

class SnrGraph(Aggregator):
    def __init__(self, url, interval=1, pub=False, filter=''):
        feeds = [(url, 'packet-in')]
        Aggregator.__init__(self, feeds)
        self.g = nx.DiGraph()
        self.interval = interval
        self.is_pub = pub
        self.url = url
        self.filter = filter
        self.bpf = pcapy.compile(127, 1500, self.filter, 0, 1)
        self.snrs = {}
        self.results = []

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
            if rdtap.ant_sig_present:
                snr = rdtap.ant_sig.db - (-90)
            else:
                snr = 0
            #seq = socket.ntohs(ieee_pkt.data_frame.frag_seq)
            seq = 0
            pkts += 1
            try:
                self.g[src][id]['snr'].append((ts,seq,snr))
                self.g[src][id]['active'] = (id == bssid)
            except KeyError:                
                self.g.add_node(src,bssid=bssid)
                self.g.add_node(id,bssid='')
                self.g.add_edge(src,id,snr=[(ts,seq,snr)],active=(id==bssid))
            if ts - last_ts > self.interval and pkts > 0:
                client_nodes = self.get_client_nodes()
                weak_nodes = self.detect_weak_nodes(-5,25)
                good_nodes = self.detect_weak_nodes(25,100)
                ap_nodes = [node for node in self.g.nodes() if self.g.in_degree(node) > 0]
                #good_nodes = self.detect_connectivity_degree()                
                neighbors = self.detect_neighbors()
                self.results.append([self.g.nodes,client_nodes,weak_nodes,good_nodes,neighbors])

                active_weak_nodes = [node for node in weak_nodes if max([l[1] for l in node[1]]) > 10]
                active_good_nodes = [node for node in good_nodes if max([l[1] for l in node[1]]) > 10]


                #print "%d,%d,%d,%d,%d" % (len(self.g.nodes()),len(client_nodes), len(weak_nodes), len(good_nodes), len(neighbors))
                print "###################################################"
                print "Weak Nodes"
                list = ["NODE : %s PKTS : %s SNRs : %s" % (node[0],max([l[1] for l in node[1]]),[l[0] for l in node[1]]) for node in active_weak_nodes]
                print "\n".join(list)
                print "\n"
                print "Good Nodes"
                list = ["NODE : %s PKTS : %s SNRs : %s" % (node[0],max([l[1] for l in node[1]]),[l[0] for l in node[1]]) for node in active_good_nodes]
                print "\n".join(list)
                print "\n\n"

                self.update_packet_list()
                self.snrs = {}
                last_ts = ts

            if time.time() - first_ts > 10:
                #nx.write_gpickle(self.g,'graph_pickle_channel11_%d.pkl' % time.time())
                self.generate_weak_links_map()
                
                first_ts = time.time()
                # f = open('graph-%d.txt' % time.time(),'w')
                # pickle.dump(self.results,f)
                # f.close()
                # self.results = []
            

    def generate_weak_links_map(self):
        weak_nodes = self.detect_weak_nodes(-5,25)
        active_weak_nodes = [node[0] for node in weak_nodes if max([l[1] for l in node[1]]) > 10]
        ap_nodes = [node for node in self.g.nodes() if self.g.in_degree(node) > 0]

        edges = self.g.edges(active_weak_nodes)
        snr_g = nx.DiGraph()
        snr_g.add_nodes_from(active_weak_nodes + ap_nodes)
        snr_g.add_edges_from(edges)
        
        for node in active_weak_nodes:
            snr_g.node[node]['type'] = 'sta'
        for node in ap_nodes:
            snr_g.node[node]['type'] = 'ap'
                

        nx.write_gpickle(snr_g,'graph_pickle_connectivity_%d.pkl' % time.time())
        #nx.draw(snr_g,with_labels=False)
        #pylab.savefig("connectivity-graph-%d.png" % (int(time.time())))

        d = json_graph.node_link_data(snr_g) # node-link format to serialize
        # write json 
        json.dump(d, open('force/force.json','w'))


        print ap_nodes

    def update_packet_list(self):
        for src,dst,data in self.g.edges(data=True):
            pkts = [s for s in data['snr'] if time.time() - s[0] < 60]
            if len(pkts) == 0:
                self.g.remove_edge(src,dst)
                for node in src,dst:
                    if self.g.in_degree(node) == 0 and self.g.out_degree(node) == 0:
                        self.g.remove_node(node)
            else:
                self.g[src][dst]['snr'] = pkts

    def get_client_nodes(self):
        client_nodes = [node for node in self.g.nodes() if self.g.in_degree(node) == 0]
        client_nodes = [node for node in client_nodes if node != None and (node[2:6] != "180a" and node[0:6] != "008048")]
        return client_nodes

    def detect_ofwifi_nodes(self):
        client_nodes = [(node,data) for node,data in self.g.nodes(True) if self.g.in_degree(node) == 0]
        #ofwifi_nodes = [str((node,data['bssid'],self.g.out_edges(node))) for node,data in client_nodes if data['bssid'] != None and data['bssid'].startswith('008048')]
        ofwifi_nodes = [node for node,data in client_nodes if data['bssid'] != None and data['bssid'].startswith('008048')]
        return ofwifi_nodes

    def detect_active_links(self):
        return [(src,dst) for src,dst,data in self.g.out_edges(data=True) if data['active'] == True]

    def detect_active_weak_links(self):
        weak_nodes = []
        active_links = self.detect_active_links()
        for link in active_links:
            snrs = [d[2] for d in self.g[link[0]][link[1]]['snr']]
            avg_snr = sum(snrs)/len(snrs)
            if avg_snr < SNR_ALERT_THRESHOLD and avg_snr != 0:
                weak_nodes.append((link[0],link[1],avg_snr,len(snrs)))
        weak_nodes = sorted(weak_nodes, key=lambda l:l[0])
        return weak_nodes
        # str_weak_nodes = [str(n) for n in weak_nodes]
        # print "Active weak nodes"
        # print "\n".join(str_weak_nodes)
        # print "\n\n"
        

    def detect_connectivity_degree(self):
        strong_nodes = []
        client_nodes = [node for node,data in self.g.nodes(True) if self.g.in_degree(node) == 0 and self.g.out_degree(node) > 0]
        client_nodes = [n for n in client_nodes if n != None and (n[2:6] != "180a" and n[0:6] != "008048")]

        for node in client_nodes:
            snrs = []
            for src,dst,data in self.g.out_edges(node,True):
                snr_data = [d[2] for d in data['snr']]
                snrs.append((sum(snr_data)/len(snr_data), len(snr_data)))

            good_nodes = [s for s in snrs if s[0] >= SNR_ALERT_THRESHOLD]
            if len(good_nodes) > 0:
                strong_nodes.append((node,good_nodes))
        strong_nodes = sorted(strong_nodes, key = lambda l:len(l[1]))
        return strong_nodes
        
        # print "Good Nodes"
        # print "%d Good Nodes detected (out of %d nodes)" % (len(strong_nodes),len(client_nodes))
        # for node in strong_nodes:
        #     print "Good Node : %s (%d, %s)" % (node[0], len(node[1]), node[1])

    def plot_graph(self):        
        client_nodes = [node for node,data in self.g.nodes(True) if self.g.in_degree(node) == 0 and self.g.out_degree(node) > 0]
        client_nodes = [n for n in client_nodes if n!= None and (n[2:6] != "180a" and n[0:6] != "008048")]
        ap_nodes = [node for node in self.g.nodes() if self.g.in_degree(node) > 0]
        pylab.figure()
        nx.draw(self.g, nodelist = client_nodes + ap_nodes, edgelist = self.g.edges(client_nodes), with_labels=False, )
        pylab.savefig("graph-%d.png" % int(time.time()))

    def plot_connectivity_graph(self, nodes=[],aps=[]):
        pylab.figure()

        for node in nodes:
            node['type'] = 'sta'
        for ap in aps:
            ap['type'] = 'ap'
        edges = self.g.edges(nodes)
        snr_g = nx.DiGraph()
        snr_g.add_nodes_from(_nodes + aps)
        snr_g.add_edges_from(edges)

        nx.write_gpickle(snr_g,'graph_pickle_connectivity_%d.pkl' % time.time())
        nx.draw(snr_g,with_labels=False)
        pylab.savefig("connectivity-graph-%d.png" % (int(time.time())))

        d = json_graph.node_link_data(snr_g) # node-link format to serialize
        # write json 
        json.dump(d, open('force/force.json','w'))


    def detect_neighbors(self):
        ap_nodes = [node for node in self.g.nodes() if self.g.in_degree(node) > 0]
        nns = [(node, self.g.in_degree(node)) for node in ap_nodes]
        nns = sorted(nns,key = lambda l:l[1], reverse=True)

        return nns

        # for n in nns:
        #     print n[0],n[1]

    def detect_weak_nodes(self, threshold_min, threshold_max):
        #print len(self.g.nodes())
        ap_nodes = [node for node in self.g.nodes() if self.g.in_degree(node) > 0]
        client_nodes = [node for node,data in self.g.nodes(True) if self.g.in_degree(node) == 0 and self.g.out_degree(node) > 0]
        client_nodes = [n for n in client_nodes if n != None and (n[2:6] != "180a" and n[0:6] != "008048")]

        client_nodes = self.detect_ofwifi_nodes()

        weak_nodes = []

        for node in client_nodes:
            snrs = []
            for src,dst,data in self.g.out_edges(node,True):
                snr_data = [d[2] for d in data['snr']]
                snrs.append((sum(snr_data)/len(snr_data), len(snr_data)))
                
            if max([s[0] for s in snrs]) < threshold_max and max([s[0] for s in snrs]) > threshold_min:
                weak_nodes.append((node,snrs))

        weak_nodes = sorted(weak_nodes,key = lambda l: max([n[1] for n in l[1]]),reverse=True)
        return weak_nodes

        # print "%d Weak Nodes detected (out of %d nodes)" % (len(weak_nodes),len(client_nodes))
        # for weak_node in weak_nodes:
        #     print "Weak Node : %s (%s)" % (weak_node[0],weak_node[1])
        # print "\n\n"

