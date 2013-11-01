#!/usr/bin/env python
import sys
import string
from subprocess import *
import re
import time
from optparse import OptionParser
from util_ap import *
from GenericSampler import GenericSampler
from UdpJsonTransmitter import UdpJsonTransmitter
#import pymongo
#from pymongo.errors import AutoReconnect

class ChUtilSampler(GenericSampler):
  def __init__(self, intf, fake=False, description=''):

      self.intf = intf
      self.fake = fake
      self.description = description

      self.CMD_SURVEY="iw dev %s survey dump" % self.intf

      self.mac_addr = get_mac_address(INTF)
      print self.mac_addr
      #hostname = get_hostname()
      self.hostname = 'deadbeef'

      if self.fake:
	  self.last_raw_utils = self.init_stats_sim()
      else:
	  self.last_raw_utils = self.init_stats()


  def switch_channel(self, channel):
      pipe = Popen("iwconfig %s channel %d" % (self.intf,channel), shell=True, stdout=PIPE)
      out, err = pipe.communicate()
      if (err):
	  print "switch channel failed - exiting..." % err
	  sys.exit(0)

  def parse_iw_output(self, str):
      utils = []
      for line in string.split(str,"\n"):
	  if line.lstrip().startswith("frequency"):
	      _line = line[line.find(":")+1:]
	      m = re.match(r"\s+(?P<val>\w+) MHz", _line.rstrip())
	      freq = m.group('val')
	  if line.lstrip().startswith("channel active time"):
	      _line=line[line.find(":")+1:]
	      m = re.match(r"\s+(?P<val>\w+) ms",_line.rstrip())
	      active_time = int(m.group('val'))
	  if line.lstrip().startswith("channel busy time"):
	      _line=line[line.find(":")+1:]
	      m = re.match(r"\s+(?P<val>\w+) ms",_line.rstrip())
	      busy_time = int(m.group('val'))
	  if line.lstrip().startswith("channel receive time"):
	      _line=line[line.find(":")+1:]
	      m = re.match(r"\s+(?P<val>\w+) ms",_line.rstrip())
	      receive_time = int(m.group('val'))
	  if line.lstrip().startswith("channel transmit time"):
	      _line=line[line.find(":")+1:]
	      m = re.match(r"\s+(?P<val>\w+) ms",_line.rstrip())
	      transmit_time = int(m.group('val'))
	      #print "%s:%d,%d,%d,%d" % (freq,active_time,busy_time,receive_time,transmit_time)
	      utils.append({'timestamp':time.time(),'mac_addr':self.mac_addr,'hostname':self.hostname,'freq':freq,'intf':self.intf,
			    'active':active_time,'busy':busy_time,'receive':receive_time,'transmit':transmit_time, 'description':self.description})
      return utils
      

  def update_stats_sim(self, last_raw_utils):
      utils = [{'timestamp':time.time(),'mac_addr':self.mac_addr,'hostname':self.hostname,'freq':"2412",
	       'active':1000,'busy':600,'receive':200,'transmit':200, 'intf':self.intf,'description':self.description}]
      return last_raw_utils,utils

  def init_stats_sim(self):
      return [{'timestamp':time.time(),'mac_addr':self.mac_addr,'hostname':self.hostname,'freq':"2412",
	      'active':1000,'busy':600,'receive':200,'transmit':200, 'intf':self.intf,'description':self.description}]

  def init_stats(self):
      pipe = Popen(CMD_SURVEY,shell=True,stdout=PIPE)
      out,err = pipe.communicate()
      if (err):
	  print "iw failed - exiting...(%s)" % err
	  sys.exit(0)
      else:
	  raw_utils = parse_iw_output(out)
	  return raw_utils
      
  def update_stats(self, last_raw_utils):
      pipe = Popen(CMD_SURVEY,shell=True,stdout=PIPE)
      out,err = pipe.communicate()
      if (err):
	  print "iw failed - exiting...(%s)" % err
	  sys.exit(0)
      else:
	  raw_utils = parse_iw_output(out)
	  utils = []
	  for raw_util,last_raw_util in zip(raw_utils, last_raw_utils):
	      utils.append({'timestamp':raw_util['timestamp'],'freq':raw_util['freq'],'mac_addr':self.mac_addr,'hostname':self.hostname, 'intf':self.intf,'description':self.description,
			    'active':raw_util['active'] - last_raw_util['active'],
			    'busy':raw_util['busy'] - last_raw_util['busy'],
			    'receive':raw_util['receive'] - last_raw_util['receive'],
			    'transmit':raw_util['transmit'] - last_raw_util['transmit']})
	  return raw_utils, utils

  def next(self):
      if self.fake:
	  self.last_raw_utils, last_utils = self.update_stats_sim(self.last_raw_utils)
      else:
	  self.last_raw_utils, last_utils = self.update_stats(self.last_raw_utils)

      return last_utils


def log_stats(self, utils):
    for util in utils:
	if util['active'] != 0:
	    if options.verbose:
		print "%s" % (util)
	    #if options.mongo:
	    #    try:
	    #        if options.loop:
	    #            db.cross_stats.insert(util)
	    #        else:
	    #            db.serve_stats.insert(util)
	    #    except AutoReconnect:
	    #        print "Log to DB failed - disconnected..."
                    
if __name__=="__main__":
    parser = OptionParser()
    parser.add_option("-s","--server",dest="server",
                      default="localhost",
                      help="hostname for the aggregation server")
    parser.add_option("-p","--port",dest="port",
                      type="int", default=27017,
                      help="port for the aggregation server")
    parser.add_option("-u","--updev",dest="updev",
                      default='br0',
                      help="upward network device to send back log entries")
    #parser.add_option("-m","--mongo",dest="mongo",
    #                  action="store_true", default=False,
    #                  help="If set, send logs to a MongoDB server.")
    parser.add_option("-v","--verbose",dest="verbose",
                      action="store_true", default=False,
                      help="verbose output.")
    parser.add_option("-f","--fake",dest="fake",
                      action="store_true", default=False,
                      help="If set, simulate the wireless stats.")
    #parser.add_option("-l","--loop",dest="loop",
    #                  action="store_true", default=False,
    #                  help="If set, loop monitoring between channels 1,6,11.")
    parser.add_option("-i","--intf",dest="intf",
                      default="wlan0",
                      help="which interface to collect stats from")
    parser.add_option("-I","--interval",dest="interval",
                      type="int", default=5,
                      help="Interval between stats updates (secs)")
    parser.add_option("-d","--description",dest="description",
                      default="standard",
                      help="Description of the experiment, if any")


    (options, args) = parser.parse_args()


    

    #if options.fake:
    #    last_raw_utils = init_stats_sim()
    #else:
    #    last_raw_utils = init_stats()
    time.sleep(5)

    channels = [1,6,11]
    channel = 1

    #while(True):
    #    if options.fake:
    #        last_raw_utils, last_utils = update_stats_sim(last_raw_utils)
    #    else:
    #        last_raw_utils, last_utils = update_stats(last_raw_utils)
    #    log_stats(last_utils)
    #    #if options.loop:            
    #    #    channel = channels[(channels.index(channel) + 1) % 3]
    #    #    print "switching to channel %d" % channel
    #    #    switch_channel(channel)
    #    #    time.sleep(1)
    #    #    last_raw_utils = init_stats()
    #    time.sleep(options.interval)

    #UPWARD_DEVICE = 'br0'
    #DST_IP = "172.24.74.179"
    #DST_PORT = 5590

    UPWARD_DEVICE = options.updev
    DST_IP = options.server
    DST_PORT = options.port

    #INTF = 'wlan0'
    #FAKE = True
    INTF = options.intf
    FAKE = options.fake

    #sampler = TestSampler()
    sampler = ChUtilSampler(INTF, FAKE, options.description)

    
    #ID = get_ip_address(UPWARD_DEVICE)
    ID = get_mac_address(UPWARD_DEVICE)
    udpJsonTransmitter = UdpJsonTransmitter(sampler, DST_IP, DST_PORT, options.interval, ID)

    udpJsonTransmitter.setDaemon(True)
    udpJsonTransmitter.start()

    #TODO : stop the threads using ctrl-c
    while(True):
        time.sleep(60)

