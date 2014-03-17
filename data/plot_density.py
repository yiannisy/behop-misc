#!/usr/bin/env python
import pandas as pd

x = pd.read_csv('probes.txt',sep='|')
links = x.groupby(['client','dpid'])
link_average = links['snr'].mean()
link_count = links['band'].count()

link_average.to_csv('link_snr.csv',sep=',')
link_count.to_csv('link_count.csv',sep=',')
print link_average[:5]
print link_count[:5]
