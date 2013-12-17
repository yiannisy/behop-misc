#!/usr/bin/env python
import string,sys
import re
from optparse import OptionParser

def analyze_tcptrace(fname_in,fname_out):
    f = open(fname_in,'r')
    for line in f.readlines()[7:]:
        if line.find('unidirectional') != -1:
            continue
        p = re.compile(r'(\w+.\w+.\w+.\w+):\w+ - (\w+.\w+.\w+.\w+):\w+ \((\w+)2(\w+)\)')
        m = p.search(line)
        if m:
            ip_src = m.group(1)
            ip_dst = m.group(2)
            flow_src = m.group(3)
            flow_dst = m.group(4)
            if ip_src.startswith("10.30") and ip_dst.startswith("10.30"):
                print "SRC - DST both in network --- skipping..."
                print ip_src,ip_dst,flow_src,flow_dst
                continue
            if ip_src.startswith("10.30"):
                host = ip_src
                end = ip_dst
                flow = flow_dst + "2" + flow_src + "_rttraw.dat"
            elif ip_dst.startswith("10.30"):
                flow = flow_src + "2" + flow_dst + "_rttraw.dat"
                host = ip_dst
                end = ip_src
            rtt_fname = fname_out + flow
            host_fname = fname_out + '/rtt_%s.log' % host
            try:
                f_rtt = open(rtt_fname,'r')
                f_host = open(host_fname,'a+')
            except:
                print "cannot find file (%s,%s)" % (rtt_fname,host_fname)
                continue
            print "Analyzing flow for %s (%s)" % (host,flow)
            for line in f_rtt.readlines():
                f_host.write(line)
            f_rtt.close()
            f_host.close()
        
    f.close()

if __name__== "__main__":

    parser = OptionParser()
    parser.add_option("-i", "--input-file", dest="fname_in",
                      help="read requests from file", metavar="FILE")
    parser.add_option("-o", "--output-file", dest="fname_out",
                      help="write report to FILE", metavar="FILE")

    (options, args) = parser.parse_args()
    analyze_tcptrace(options.fname_in, options.fname_out)
