#!/usr/bin/env python
import string
from optparse import OptionParser

YOUTUBE_REQS_FNAME='.tmp/youtube_requests.txt'
NETFLIX_REQS_FNAME='.tmp/netflix_requests.txt'
YOUTUBE_LOGS_FNAME='.tmp/youtube.log'
NETFLIX_LOGS_FNAME='.tmp/netflix.log'

# the log format is as follows (two line pattern)
# ts ip_src -> ip_dst
# GET /mplamplampla

def analyze_youtube_requests(fname, fname_out):
    f = open(fname,'r')
    f_out = open(fname_out,'w')
    lines = f.readlines()
    print "Processing %d web requests from youtube" % (len(lines)/2)
    for i in range(0,len(lines)/2):
        meta_line = lines[2*i]
        req_line = string.split(lines[2*i + 1],' ')[1]
        vals = string.split(meta_line,' ')
        tstamp = vals[1] + " " + vals[2] + "-0800"
        ip_src = string.split(vals[3],':')[0]
        ip_dst = string.split(vals[5],':')[0]

        req_line = string.split(req_line,'?')[1]
        vals = string.split(req_line,'&')
        req = {}
        for val in vals:
            _v = string.split(val,'=')
            req[_v[0]] = _v[1]

        if not req.has_key('range') or not req.has_key('dur'):
            print "cannot extract range/dur---skip request."
            continue
        # calculate the range length
        _v = string.split(req['range'],'-')
        _v = [int(_v[0]),int(_v[1])]
        req_len = _v[1] - _v[0]
        req['dur'] = float(req['dur'])
        # calculate the rate (rate = length_in_bits/duration)
        req_rate = req_len/req['dur']

        f_out.write("%s,%s,%s,%d,%f,%f,%s\n" % (tstamp,ip_src,ip_dst,req_len,req_rate,req['dur'],req['range']))
    f.close()
    f_out.close()


def analyze_netflix_requests(fname, fname_out):
    f = open(fname,'r')
    f_out = open(fname_out,'w')
    lines = f.readlines()
    print "Processing %d web requests from netflix" % (len(lines)/2)
    for i in range(0,len(lines)/2):
        meta_line = lines[2*i]
        request_line = lines[2*i + 1]
        vals = string.split(meta_line,' ')
        tstamp = vals[1] + " " + vals[2] + "-0800"
        ip_src = string.split(vals[3],':')[0]
        ip_dst = string.split(vals[5],':')[0]
	
        req_line = string.split(request_line,'?')[0]
        vals = string.split(req_line,'/')
        req_range = vals[-1]
        # calculate the range length
        _v = string.split(req_range,'-')
        _v = [int(_v[0]),int(_v[1])]
        req_len = (_v[1] - _v[0])*8
        req_dur = 4000
        # calculate the rate (rate = length_in_bits/duration)
        req_rate = req_len/req_dur

        param_line = string.split(request_line,'?')[1]
        vals = string.split(param_line,'&')
        req = {}
        for val in vals:
            _v = string.split(val,'=')
            req[_v[0]] = _v[1]

        if not req.has_key('p'):
            print "cannot extract session-id---skip request."
            continue

	
        f_out.write("%s,%s,%s,%d,%f,%f,%s,%s\n" % (tstamp,ip_src,ip_dst,req_len,req_rate,req_dur,req_range,req['p']))
    f.close()
    f_out.close()

if __name__== "__main__":

    parser = OptionParser()
    parser.add_option("-i", "--input-file", dest="fname_in",
                      help="read requests from file", metavar="FILE")
    parser.add_option("-o", "--output-file", dest="fname_out",
                      help="write report to FILE", metavar="FILE")
    parser.add_option("-s", "--service",
                      help="which service to analyze (netflix or youtube)",
                      dest="service")

    (options, args) = parser.parse_args()
    if options.service == "netflix":
        analyze_netflix_requests(options.fname_in, options.fname_out)
    elif options.service == "youtube":
        analyze_youtube_requests(options.fname_in, options.fname_out)
    else:
        print "unknown service : %s" % options.service
    
