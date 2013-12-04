#!/usr/bin/env python
import string

YOUTUBE_REQS_FNAME='.tmp/youtube_requests.txt'
NETFLIX_REQS_FNAME='.tmp/netflix_requests.txt'
YOUTUBE_LOGS_FNAME='.tmp/youtube.log'
NETFLIX_LOGS_FNAME='.tmp/netflix.log'

# the log format is as follows (two line pattern)
# ts ip_src -> ip_dst
# GET /mplamplampla


f = open(YOUTUBE_REQS_FNAME,'r')
f_out = open(YOUTUBE_LOGS_FNAME,'w')
lines = f.readlines()
print "Processing %d web requests from youtube" % (len(lines)/2)
for i in range(0,len(lines)/2):
    meta_line = lines[2*i]
    req_line = lines[2*i + 1]
    vals = string.split(meta_line,' ')
    tstamp = vals[1] + "-" + vals[2]
    ip_src = string.split(vals[3],':')[0]
    ip_dst = string.split(vals[5],':')[0]

    req_line = string.split(req_line,'?')[1]
    vals = string.split(req_line,'&')
    req = {}
    for val in vals:
        _v = string.split(val,'=')
        req[_v[0]] = _v[1]
          
    # calculate the range length
    _v = string.split(req['range'],'-')
    _v = [int(_v[0]),int(_v[1])]
    req_len = _v[1] - _v[0]
    req['dur'] = float(req['dur'])
    # calculate the rate (rate = length_in_bits/duration)
    req_rate = req_len/req['dur']

    f_out.write("%s,%s,%s,%d,%f,%f,%s" % (tstamp,ip_src,ip_dst,req_len,req_rate,req['dur'],req['range']))
f.close()
f_out.close()

f = open(NETFLIX_REQS_FNAME,'r')
f_out = open(NETFLIX_LOGS_FNAME,'w')
lines = f.readlines()
print "Processing %d web requests from netflix" % (len(lines)/2)
for i in range(0,len(lines)/2):
    meta_line = lines[2*i]
    req_line = lines[2*i + 1]
    vals = string.split(meta_line,' ')
    tstamp = vals[1] + "-" + vals[2]
    ip_src = string.split(vals[3],':')[0]
    ip_dst = string.split(vals[5],':')[0]

    req_line = string.split(req_line,'?')[0]
    vals = string.split(req_line,'/')
    req_range = vals[-1]
    # calculate the range length
    _v = string.split(req_range,'-')
    _v = [int(_v[0]),int(_v[1])]
    req_len = (_v[1] - _v[0])*8
    req_dur = 4000
    # calculate the rate (rate = length_in_bits/duration)
    req_rate = req_len/req_dur

    f_out.write("%s,%s,%s,%d,%f,%f,%s" % (tstamp,ip_src,ip_dst,req_len,req_rate,req_dur,req_range))
f.close()
f_out.close()
