#!/usr/bin/env python
import aggregators
import time
import sys

POLL_INTERVAL = 5
INTF='wlan1'


if len(sys.argv) > 1:
    POLL_INTERVAL = int(sys.argv[1])
if len(sys.argv) > 2:
    INTF = sys.argv[2]

if __name__ == "__main__":
    aggs = []
    collector = aggregators.Collector(intf=INTF)
    packet_collector_url = "tcp://swan-ap2.stanford.edu:%s" % 5556
    #aggs.append(aggregators.LinkAggregator(packet_collector_url,interval=POLL_INTERVAL))
    #aggs.append(aggregators.NodeAggregator(packet_collector_url, interval=POLL_INTERVAL))
    #aggs.append(aggregators.ApAggregator(packet_collector_url, interval=POLL_INTERVAL))
    aggs.append(aggregators.HomeAggregator(packet_collector_url, interval=POLL_INTERVAL))             
    for agg in aggs:
        agg.setDaemon(True)
        agg.start()

    collector.setDaemon(True)
    collector.start()

    #TODO : stop the threads using ctrl-c
    while(True):
        time.sleep(60)
