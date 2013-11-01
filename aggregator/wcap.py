#!/usr/bin/env python

import cmd,sys
import time
from aggregators import *
from graphs import SnrGraph
from service import ServiceStats
#from query import QueryServer
from query import QueryTCPClient
import traceback
from conf import *

aps = [2,3,5,8,10,11,12,13,14,19,21,22,23,24,25,26,27,28,30]
#aps = [2]
all_nodes = ['swan-ap%d.stanford.edu' % i for i in aps]
all_nodes.append('swan-ap15-ctl.stanford.edu')

active_aggs = []

def run_aggregate_cmd(nodes=[],interval=60, filter=filter):
    aggs = []
    for node in nodes:
        print "waiting for events from %s" % node
        packet_collector_url = "tcp://%s:%s" % (node, 5556)
        aggs.append(HomeAggregator(packet_collector_url,interval=interval, filter=filter))

    for agg in aggs:
        agg.setDaemon(True)
        agg.start()

    #TODO : stop the threads using ctrl-c
    while(True):
        try:
            time.sleep(60)
        except KeyboardInterrupt as e:
            stop_aggregators(aggs)
            break
    
       
def run_utility_cmd(nodes=[],filter=''):
    aggs = []
    packet_collector_url = "tcp://localhost:%d" % PROXY_SUBSCRIBER
    snr_agg = UtilityAggregator(packet_collector_url, interval=1,filter=filter)
    snr_agg.setDaemon(True)
    snr_agg.start()

    #TODO : stop the threads using ctrl-c
    while(True):
        try:
            time.sleep(60)
        except KeyboardInterrupt as e:
            stop_aggregators([snr_agg])
            break

    
#    
#    for node in nodes:
#        packet_collector_url = "tcp://%s:%s" % (node, 5556)
#        aggs.append(UtilityAggregator(packet_collector_url,interval=1,filter=filter))
#
#    for agg in aggs:
#        agg.setDaemon(True)
#        agg.start()
#
#    active_aggs = [agg for agg in aggs]
#
#    #TODO : stop the threads using ctrl-c
#    while(True):
#        try:
#            time.sleep(60)
#        except KeyboardInterrupt as e:
#            stop_aggregators(aggs)
#            break

def run_snr_graph_cmd(nodes=[]):
    packet_collector_url = "tcp://localhost:%d" % PROXY_SUBSCRIBER
    snr_graph = SnrGraph(packet_collector_url, interval=5)
    snr_graph.setDaemon(True)
    snr_graph.start()

    while(True):
        try:
            time.sleep(60)
        except KeyboardInterrupt as e:
            stop_aggregators([snr_graph])
            break

def run_service_stats_cmd(nodes=[]):
    packet_collector_url = "tcp://localhost:%d" % PROXY_SUBSCRIBER
    service_stats = ServiceStats(packet_collector_url, interval=5)
    service_stats.setDaemon(True)
    service_stats.start()

    while(True):
        try:
            time.sleep(60)
        except KeyboardInterrupt as e:
            stop_aggregators([service_stats])
            break

def run_snr_cmd(nodes=[],filter=''):
    '''Collects packet-ins from all nodes.
    Maintains a list for each node-AP pair with the SNR packet history.
    '''
    aggs = []
    packet_collector_url = "tcp://localhost:%d" % PROXY_SUBSCRIBER
    snr_agg = SnrAggregator(packet_collector_url, interval=5,filter=filter)
    snr_agg.setDaemon(True)
    snr_agg.start()

    #TODO : stop the threads using ctrl-c
    while(True):
        try:
            time.sleep(60)
        except KeyboardInterrupt as e:
            stop_aggregators([snr_agg])
            break



def run_link_cmd(nodes=[], filter=''):
    aggs = []
    for node in nodes:
        packet_collector_url = "tcp://%s:%s" % (node, 5556)
        aggs.append(NodeAggregator(packet_collector_url,interval=1,filter=filter))

    for agg in aggs:
        agg.setDaemon(True)
        agg.start()

    active_aggs = [agg for agg in aggs]

    #TODO : stop the threads using ctrl-c
    while(True):
        try:
            time.sleep(60)
        except KeyboardInterrupt as e:
            stop_aggregators(aggs)
            break


def run_pi_cmd(parent, filter='', nodes=[]):
    try:
      packet_collector_url = "tcp://localhost:%d" % PROXY_SUBSCRIBER
      pi_aggr = PiAggregator(packet_collector_url, interval=5)

      pi_aggr.get_info_base().init_queries()
      qs = pi_aggr.get_info_base().get_queries_provided()
      print 'pi provides these queries:', qs
      #parent.queryServer.register_query_provider(pi_aggr, qs)
      parent.queryTCPClient.register_query_provider(pi_aggr, qs)

      pi_aggr.setDaemon(True)
      pi_aggr.start()

      while(True):
	  try:
	      time.sleep(60)
	  except KeyboardInterrupt as e:
	      stop_aggregators([pi_aggr])
	      break

    except Exception as e:
      print '-'*60
      print e
      traceback.print_exc(file=sys.stdout)
      print '-'*60

def run_piudp_cmd(parent, TEST_MODE, filter=DEF_AGG_FILTER, nodes=[]):
    try:
      print 'creating piudp aggregator'
      print 'TEST_MODE: %s' % TEST_MODE
      pi_aggr = PiUdpAggregator(TEST_MODE, interval=5, filter=filter)

      print 'initializing piudp infobase queries'
      pi_aggr.get_info_base().init_queries()
      qs = pi_aggr.get_info_base().get_queries_provided()

      print 'piudp provides these queries:', qs
      #parent.queryServer.register_query_provider(pi_aggr, qs)

      print 'registering piudp infobase'
      parent.queryTCPClient.register_query_provider(pi_aggr, qs)

      print 'starting piudp thread'
      pi_aggr.setDaemon(True)
      pi_aggr.start()
      print 'started piudp thread'

      while(True):
	  try:
	      time.sleep(60)
	  except KeyboardInterrupt as e:
	      stop_aggregators([pi_aggr])
	      break

    except Exception as e:
      print '-'*60
      print e
      traceback.print_exc(file=sys.stdout)
      print '-'*60


def run_piudpchutil_cmd(parent, args):
    try:
      ip = args[0]
      port = int(args[1])
      print 'creating piudpchutil aggregator'
      pichutil_aggr = PiUdpChUtilAggregator(ip, port, interval=5)

      #print 'initializing piudpchutil infobase queries'
      #pichutil_aggr.get_info_base().init_queries()
      #qs = pichutil_aggr.get_info_base().get_queries_provided()

      #print 'piudpchutil provides these queries:', qs
      ##parent.queryServer.register_query_provider(pichutil_aggr, qs)

      #print 'registering piudpchutil infobase'
      #parent.queryTCPClient.register_query_provider(pichutil_aggr, qs)

      print 'starting piudpchutil thread'
      pichutil_aggr.setDaemon(True)
      pichutil_aggr.start()
      print 'started piudpchutil thread'

      while(True):
	  try:
	      time.sleep(60)
	  except KeyboardInterrupt as e:
	      stop_aggregators([pichutil_aggr])
	      break

    except Exception as e:
      print '-'*60
      print e
      traceback.print_exc(file=sys.stdout)
      print '-'*60

def stop_aggregators(active_aggs):
    for agg in active_aggs:
        agg.stop()

class Wcap(cmd.Cmd):
    intro = 'wcap. Type help or ? to list commands.\n'
    prompt = 'wcap> '

    def __init__(self):
        cmd.Cmd.__init__(self)

	#self.queryServer = QueryServer()
	#self.queryServer.start()

	self.queryTCPClient = QueryTCPClient()
	#self.queryTCPClient.start()

        self.proxy = Proxy()
        self.proxy.setDaemon(True)
        self.proxy.start()

    def do_scan_homes(self, arg):
        'Scanning for homes from a given node.'
        print "scanning for homes!" #% arg
        print arg
        if arg == '':
            nodes = all_nodes
            filter = 'type mgt'
        else:
            vals = arg.split()
            nodes = [vals[0]]
            print vals
            print nodes
        if len(arg) > len(nodes[0]):
            filter = arg[arg.find(' ')+1:]
        run_aggregate_cmd(nodes=nodes, interval=5, filter=filter)

    def do_utility_all(self, arg):
        'Get the utility for the traffic as defined in the argument.'
        print "scanning for utility : %s" % arg
        run_utility_cmd(filter=arg, nodes=all_nodes)

    def do_utility(self, arg):
        'Get the utility for the traffic from the specific AP.'
        filter = ''
        vals = arg.split()
        nodes = [vals[0]]
        if len(arg) > len(nodes[0]):
            filter = arg[arg.find(' ')+1:]
        print nodes
        print filter
        run_utility_cmd(filter=filter, nodes=nodes)

    def do_snr(self, arg):
        'Get the utility for the traffic from the specific AP.'
        filter = ''
        filter = arg
        nodes = all_nodes
        print nodes
        print filter
        run_snr_cmd(filter=filter, nodes=nodes)

    def do_snr_graph(self,arg):
        run_snr_graph_cmd(nodes=all_nodes)

    def do_service_stats(self,arg):
	run_service_stats_cmd()

    def do_pi(self,arg):
        filter = arg
	print 'Running pi aggregator with filter=%s' % filter
	run_pi_cmd(self, filter)

    def do_piudp(self,arg):
        TEST_MODE = False
	print 'arg=%s' % arg
	#raw_input()
    	if len(arg) > 0:
	  if arg[0] == 'test':
	    #filter = arg[1:]
	    filter = ' '.join(arg[1:])
	    TEST_MODE = True
	  else:
	    #filter = DEF_AGG_FILTER + ' and (' + arg + ')'
	    filter = arg
	else:
	  filter = DEF_AGG_FILTER
	if TEST_MODE:
	  print 'Running piudp (TEST_MODE) aggregator with filter=%s' % filter
	else:
	  print 'Running piudp aggregator with filter=%s' % filter
	run_piudp_cmd(self, TEST_MODE, filter)

    def do_piudpchutil(self,arg):
	print 'arg=%s' % arg
	#raw_input()
	print 'Running piudpchutil aggregator' 
	run_piudpchutil_cmd(self, arg)

    def do_link(self,arg):
        'Get the links for the traffic from the specific AP.'
        filter = ''
        vals = arg.split()
        nodes = [vals[0]]
        if len(arg) > len(nodes[0]):
            filter = arg[arg.find(' ')+1:]
        print nodes
        print filter
        run_link_cmd(filter=filter, nodes=nodes)


    def do_exit(self, args):
    	#self.queryServer.stop()
    	self.queryTCPClient.stop()
        return -1

    def do_EOF(self, args):
        print "^D \n Bye bye!!"
        return self.do_exit(args)

    def do_ls(self,args):
    	print "Currently installed aggregators:"
	for agg in active_aggs:
	  print agg
        
    def cmdloop(self):
        try:
            cmd.Cmd.cmdloop(self)
        except KeyboardInterrupt as e:
            stop_aggregators(active_aggs)
            self.cmdloop()


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'piudp':
      if len(sys.argv) > 2:
	Wcap().do_piudp(sys.argv[2:])
      else:
	Wcap().do_piudp([])
    if len(sys.argv) > 1 and sys.argv[1] == 'piudpchutil':
      if len(sys.argv) > 2:
	Wcap().do_piudpchutil(sys.argv[2:])
      else:
	Wcap().do_piudpchutil([])
    else:
      Wcap().cmdloop()
