#!/usr/bin/env python
from plot_defaults import *

# Plots RTT files for BeHop
# Each file is given in the form "ip_addr,timestamp,tcp_seq,rtt_usec" 

s4_rtts = defaultdict(list)
s4_path="./rtt-analysis/studio4_rtts/"
s4_path="./rtt-2014-03-16/"
s5_rtts = defaultdict(list)
s5_path="./rtt-2014-03-18/"

to_plot = []
#files = os.listdir(s4_path)
#files = [f for f in files if f.startswith("rtt_10.30")]

parser = argparse.ArgumentParser(description="Plotting script.")
parser.add_argument('--files',default=None,nargs='+',help='files to read rtts from')
args = parser.parse_args()

def rtt_all(files):
    to_plot = []
    rtt_a = []
    rtt_b = []

    f = open(files[0],'r')
    for l in f.readlines()[1:]:
        ip,ts,seq,rtt = string.split(l.rstrip(),',')
        rtt_a.append(float(rtt)/1000.0)
    f.close()
    to_plot.append([rtt_a,'BeHop','g'])


    f = open(files[1],'r')
    for l in f.readlines()[1:]:
        ip,ts,seq,rtt = string.split(l.rstrip(),',')
        rtt_b.append(float(rtt)/1000.0)
    f.close()
    to_plot.append([rtt_b,'LWAPP','r'])

    plot_cdf(to_plot,'pdt_all',legend=True,xlogscale=True,
             xlabel='PDT (ms)',ylabel='CDF',alpha=0.5,xlim=[0.1,10**5])

def rtt_client(files):
    to_plot = []
    rtt_a = defaultdict(list)
    rtt_b = defaultdict(list)

    f = open(files[0],'r')
    for l in f.readlines():
        ip,vals = string.split(l.rstrip(),',')
        ts,seq,rtt = string.split(vals,' ')
        rtt_a[ip].append(float(rtt)/1000.0)
    f.close()
    for k,v in rtt_a.items():
        to_plot.append([v,'BeHop','g'])


    f = open(files[1],'r')
    for l in f.readlines():
        ip,vals = string.split(l.rstrip(),',')
        ts,seq,rtt = string.split(vals,' ')
        rtt_b[ip].append(float(rtt)/1000.0)
    f.close()
    for k,v in rtt_b.items():
        to_plot.append([v,'LWAPP','r'])

    plot_cdf(to_plot,'pdt_client',legend=False,xlogscale=True,
             xlabel='PDT (ms)',ylabel='CDF',alpha=0.5,xlim=[0.1,10**5])

def rtt_client_time(files):
    to_plot_a = []
    to_plot_b = []
    to_plot = []
    rtt_a = defaultdict(list)
    rtt_b = defaultdict(list)
    # now we need to go through each client and break it into 1-min buckets.
    rtt_mins_a = defaultdict(list)
    rtt_mins_b = defaultdict(list)

    time_rtts = []

    f = open(files[0],'r')
    for l in f.readlines():
        ip,vals = string.split(l.rstrip(),',')
        ts,seq,rtt = string.split(vals,' ')
        rtt_a[ip].append((float(ts),float(rtt)/1000.0))
    f.close()

    f = open(files[1],'r')
    for l in f.readlines():
        ip,vals = string.split(l.rstrip(),',')
        ts,seq,rtt = string.split(vals,' ')
        rtt_b[ip].append((float(ts),float(rtt)/1000.0))
    f.close()

    for client,rtts in rtt_a.items():
        start_ts = rtts[0][0]
        ts = start_ts
        _rtt = []
        while True:
            # go to next client if we've checked all samples.
            if len(rtts) == 0:
                break
            ts,rtt = rtts.pop(0)
            if ts - start_ts < 60:
                _rtt.append(rtt)
            else:
                if len(_rtt) > 100:
                    # add this minute summary to our lists
                    rtt_mins_a[client].append(_rtt)
                start_ts = ts
                _rtt = []    

    for client,rtts in rtt_b.items():
        start_ts = rtts[0][0]
        ts = start_ts
        _rtt = []
        while True:
            # go to next client if we've checked all samples.
            if len(rtts) == 0:
                break
            ts,rtt = rtts.pop(0)
            if ts - start_ts < 60:
                _rtt.append(rtt)
            else:
                if len(_rtt) > 100:
                    # add this minute summary to our lists
                    rtt_mins_b[client].append(_rtt)
                start_ts = ts
                _rtt = []    





        print "Completed processing for client %s : total mins : %d | %d" % (client,len(rtt_mins_a),len(rtt_mins_b))  


    plot_cdf(to_plot,'pdt_client_time',legend=False,xlogscale=True,
             xlabel='PDT (ms)',ylabel='CDF',alpha=0.1,xlim=[0.1,10**5])
    plot_cdf(to_plot_a,'pdt_client_time_a',legend=False,xlogscale=True,
             xlabel='PDT (ms)',ylabel='CDF',alpha=0.2,xlim=[0.1,10**5])
    plot_cdf(to_plot_b,'pdt_client_time_b',legend=False,xlogscale=True,
             xlabel='PDT (ms)',ylabel='CDF',alpha=0.2,xlim=[0.1,10**5])



print args.files
rtt_all(args.files)
#rtt_client(args.files)
#rtt_client_time(args.files)

