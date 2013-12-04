#!/usr/bin/env python

import sys
import os
from subprocess import *

def get_gw_ip():
    cmd = 'netstat -nr | grep -E "^(default|0.0.0.0)" | tr -s " " | cut -d " " -f 2'
    pipe = Popen(cmd,shell=True,stdout=PIPE)
    out,err = pipe.communicate()
    if (err):
        print "netstat failed - exiting...(%s)" % err
        sys.exit(0)
    else:
        line = out.split("\n")[0]
        ip_addr = line.strip()
        return ip_addr

def get_tr_ips(n=4, verbose=True):
    cmd = 'traceroute www.google.com 2>/dev/null | tr -s " " | grep -A %d -E "^ 1"' % (n-1)
    pipe = Popen(cmd,shell=True,stdout=PIPE)
    out,err = pipe.communicate()
    if (err):
        print "traderoute failed - exiting...(%s)" % err
        sys.exit(0)
    else:
        if verbose:
          print out
        lines = out.split("\n")
        ip_addrs = []
        for line in lines:
          try:
            ip_addr = line.split('(')[1].split(')')[0]
            ip_addrs.append(ip_addr)
          except:
            pass

        return ip_addrs

def ping_diff(farIp1, farIp2):
    #COUNT = 10
    COUNT = 2
    WAIT = 0.1
    SIZE = 56
    size = SIZE + 8
    TIMEOUT_WAIT = 1000   #milliseconds

    cmd1 = "ping -W %d -s %d -i %f -c 1 %s" % (TIMEOUT_WAIT, SIZE, WAIT, farIp1)
    cmd2 = "ping -W %d -s %d -i %f -c 1 %s" % (TIMEOUT_WAIT, SIZE, WAIT, farIp2)
    cmd = ("for i in `seq 1 %d`; do " % COUNT) + cmd1 + ";" + cmd2 + ";" + "done"

    pipe = Popen(cmd,shell=True,stdout=PIPE)
    out,err = pipe.communicate()
    if (err):
        print '"%s" failed - exiting...(%s)"' % (cmd, err)
        sys.exit(0)

    ## process ping output
    #print out
    out1 = [line for line in out.split('\n') if ("%d bytes from" % size) in line or "PING" in line]
    #out2 = [line for line in out.split('\n') if "round-trip" in line]
    #print out1
    pairs = []
    for e in out1:
      #print e
      if "PING" in e:
        #print pair
        e = e.split(" ")[1]
        pair = (e, "noreply")
        pairs.append(pair)
      else:
        e0, _ = pairs[-1]
        e = e.split('time=')[1]
        if e.endswith(' ms'):
          e = float(e.split(' ms')[0])
        else:
          'ping output not in ms'
          sys.exit(0)
        pair = (e0, e)
        pairs[-1] = pair

    for pair in pairs:
      print pair
    

def get_ping_time(far_ip):
    COUNT = 10
    WAIT = 0.1
    SIZE = 56
    size = SIZE + 8

    cmd = "ping -s %d -i %f -c %d %s" % (SIZE, WAIT, COUNT, far_ip)

    ## collect ping output
    pipe = Popen(cmd,shell=True,stdout=PIPE)
    out,err = pipe.communicate()
    if (err):
        print '"%s" failed - exiting...(%s)"' % (cmd, err)
        sys.exit(0)

    ## process ping output
    print out
    out1 = [line for line in out.split('\n') if ("%d bytes from" % size) in line]
    out2 = [line for line in out.split('\n') if "round-trip" in line]
    print '--'
    print out1
    print '--'
    print out2
    #line = string.split(out,"\n")[0]
    #print line

def bneck_link_bw(host, INTV=0.01, verbose=False):
  #print "host:", host
  
  #INTV = 0.0
  #INTV = 0.00001  #10us
  INTV_s = INTV/1000

  COUNT = 100
  SIZE = 1400
  size = SIZE + 8

  cmd = "sudo ping -i %d -c %d -s %d %s" % (INTV_s, COUNT, size, host)

  ## collect ping output
  pipe = Popen(cmd,shell=True,stdout=PIPE)
  out,err = pipe.communicate()
  if (err):
      print '"%s" failed - exiting...(%s)"' % (cmd, err)
      sys.exit(0)

  ## process ping output
  if verbose:
    print out
  out1 = [line for line in out.split('\n') if ("bytes from") in line]
  if len(out1) == 0:
    print 'host:%40s, ' % host,
    print 'no ping responses'
    return (0, 0, 0, 0, 0, 0, INTV)
  elif len(out1) == 1:
    print 'host:%40s, ' % host,
    print 'not enough responses'
    return (0, 0, 0, 0, 0, 0, INTV)
  
  nbytes = int(out1[0].split(' ')[0])
  icmp_seqs = [int(line.split('icmp_seq=')[1].split(' ')[0]) for line in out1]
  rtts = [float(line.split('time=')[1].split(' ')[0]) for line in out1]
  nresps = len(icmp_seqs)
  ntries = icmp_seqs[-1] - icmp_seqs[0] + 1
  agg_deltat = rtts[-1] - rtts[0]       #ms
  agg_deltat += INTV * (ntries - 1)     #ms
  #avg_deltat = agg_deltat/ntries
  agg_nbytes = nbytes * nresps * 2                     #factor of 2 because of echo request and echo reply both counting
  avg_rate = agg_nbytes * 8.0 / (agg_deltat * 1000)   #in Mbps

  avg_deltat = agg_deltat/ntries

  print 'host:%40s, ' % host,
  print 'ntries:%5d,' % ntries,
  print 'nresps:%5d,' % nresps,
  print 'agg_deltat(ms):%10.3f,' % agg_deltat,
  print 'agg_nbytes:%10d,' % agg_nbytes,
  print 'avg_rate(Mbps):%7.2f,' % avg_rate,
  print 'avg_deltat(ms):%6.3f,' % avg_deltat,
  print 'INTV(ms):%12.6f' % INTV

  return (ntries, nresps, agg_deltat, agg_nbytes, avg_rate, avg_deltat, INTV)

def main():
  #far_ip = "10.42.0.1"
  #get_ping_time(far_ip)

  farIp1 = "10.42.0.1"
  #farIp2 = "www.google.com"
  farIp2 = "171.67.215.200" #www.stanford.edu
  #farIp2 = "192.168.2.1"

  ##ping_diff(farIp1, farIp2)

  gw_ip = get_gw_ip()
  print "gw_ip:",gw_ip

  print

  ip_addrs = get_tr_ips()
  print ip_addrs
  
  print


  host = gw_ip
  (ntries, nresps, agg_deltat, agg_nbytes, avg_rate, avg_deltat, INTV) = bneck_link_bw(host, INTV=0.05)

  host = "www.google.com"
  (ntries, nresps, agg_deltat, agg_nbytes, avg_rate, avg_deltat, INTV) = bneck_link_bw(host, INTV=0.05)

  host = "www.stanford.edu"
  (ntries, nresps, agg_deltat, agg_nbytes, avg_rate, avg_deltat, INTV) = bneck_link_bw(host, INTV=0.05)

  for host in ip_addrs:
    (ntries, nresps, agg_deltat, agg_nbytes, avg_rate, avg_deltat, INTV) = bneck_link_bw(host, INTV=0.05)


if __name__ == '__main__':
  main()

