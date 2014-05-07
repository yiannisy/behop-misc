#!/usr/bin/env python
import pandas as pd
from plot_defaults import *
from IPython import embed
import dpkt
import logging
import subprocess
import datetime

parser = argparse.ArgumentParser(description="Plotting script.")
parser.add_argument('--files',default=None,nargs='+',help='files to read rtts from')
args = parser.parse_args()

def plot_broadcast_overhead():
    clients = 600
    beacon_length = 200 # bytes
    bcast_avg_load = 160 # bcast bytes per second.
    aps_per_domain = [4, 25, 150, 600]
    num_aps = [600, 25, 150, 600]
    bcast_load = [clients*bcast_avg_load*8*ap/1000.0 for ap in aps_per_domain]
    beacon_load = [beacon_length*10*8*aps/1000.0 for aps in num_aps]
    xticks = ['personal','default','dense','virtual']
    plt.figure()
    plt.plot(bcast_load,label='bcast')
    plt.plot(beacon_load,label='beacon')
    plt.xticks(range(0,4),xticks,rotation=45)
    plt.ylabel('Total BCast load (k)')
    plt.xlabel('VirtualAP per domain')
    plt.legend()
    plt.savefig('/tmp/bcast_overhead.pdf')

def read_pcap(filename,fields = [], strict = False, timeseries = False):
    if timeseries:
        fields = ["frame.time_epoch", "frame.len", "eth.src","eth.dst",
                  "eth.ethertype","eth.type","udp.srcport","udp.dstport"] + fields
    display_filters = fields if strict else []
    fieldspec = " ".join("-e %s" % f for f in fields)
    filterspec = "-R '%s'" % " and ".join(f for f in display_filters)
    options = "-r %s -n -T fields -Eheader=y" % filename
    cmd = "tshark %s %s %s" % (options, filterspec, fieldspec)
    proc = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE)

    if timeseries:
        df = pd.read_table(proc.stdout,
                           index_col = "frame.time_epoch",
                           parse_dates=True,
                           date_parser=datetime.datetime.fromtimestamp)
    else:
        df = pd.read_table(proc.stdout)
    return df
    

def get_broadcast_traffic():
    for fname in args.files:
        f = open(fname)
        logging.error("Loading broadcast traffic from %s" % f)
        df = read_pcap(fname,timeseries=True)
        bytes_per_second = df.resample("S",how="sum")
        embed()
        
plot_broadcast_overhead()
get_broadcast_traffic()

sys.exit()


nodes = []
pkts = []
for file in args.files:
    df = pd.read_csv(file)
    df.columns = ['timestamp','src','dst','noop']
    df['timestamp'] = df['timestamp'].apply(lambda x: string.split(x,'.')[0])
    pkts_per_host = df.groupby('src')
    pkts_per_min = df.groupby('timestamp')
    for name,g in pkts_per_host:
        nodes.append((name,len(g)))

    for name,g in pkts_per_min:
        print name
        pkts.append((name,len(g)))

nodes = sorted(nodes,key=lambda x:x[1])
plt.plot([n[1]for n in nodes],'*')
plt.yscale('log')
plt.savefig('/tmp/test.pdf')
plt.figure()
plt.plot([p[1] for p in pkts],'o')
plt.savefig('/tmp/pkts.pdf')

embed()
