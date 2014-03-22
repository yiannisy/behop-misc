#!/usr/bin/env python

from plot_defaults import *
import pandas as pd
import numpy as np
from IPython import embed
parser = argparse.ArgumentParser(description="Plotting script.")
parser.add_argument('--files',default=None,nargs='+',help='files to read rtts from')
args = parser.parse_args()
names = []

osx = ['10.30.68.111','10.30.68.126','10.30.68.136','10.30.84','10.30.69.140','10.30.69.17',
       '10.30.69.196','10.30.69.20','10.30.69.25','10.30.69.34','10.30.70.14','10.30.70.15','10.30.73.136',
       '10.30.68.130','10.30.68.150','10.30.69.222','10.30.69.241','10.30.71.201']
ios = ['10.30.68.151','10.30.68.232','10.30.68.30','10.30.68.51','10.30.68.53','10.30.68.88','10.30.69.107',
       '10.30.69.11','10.30.69.138','10.30.69.147','10.30.69.224','10.30.69.41','10.30.69.65','10.30.70.22','10.30.73.137','10.30.73.139','10.30.70.152']
android = ['10.30.69.153','10.30.71.184','10.30.72.215']
windows =['10.30.69.191','10.30.69.232']

def rtt_all(df1,df2):
    to_plot = []
    rtts = df1['rtt'].apply(lambda x:x/1000.0).astype('float32').values
    to_plot.append([rtts,'BeHop','g'])

    rtts = df2['rtt'].apply(lambda x:x/1000.0).astype('float32').values
    to_plot.append([rtts,'LWAPP','r'])

    plot_cdf(to_plot,'pdt_all',legend=True,xlogscale=True,
             xlabel='PDT (ms)',ylabel='CDF',alpha=0.5,xlim=[0.1,10**5])

def rtt_client_time(df1,df2):
    to_plot_behop = []
    to_plot_lwapp = []
    to_plot = []
    to_plot_clients = defaultdict(list)
    to_plot_os = defaultdict(list)

    g = df1.groupby('ip')
    for name, group in g:
        if name not in osx:
            continue
        names.append(name)
        to_plot_client = []
        mins = group.groupby('timestamp_min')
        for min, group_min in mins:
            num, blah = group_min.values.shape
            if num < 100:
                continue
            rtts = group_min['rtt'].apply(lambda x:x/1000.0).values
            # compute CDF here and save to figure?
            # OK :) i need netflix coupon
            to_plot.append([rtts,'BeHop','g'])
            to_plot_behop.append([rtts,'BeHop','g'])
            to_plot_clients[name].append([rtts,'BeHop','g'])

    g = df2.groupby('ip')
    for name, group in g:
        names.append(name)
        if name not in osx:
            continue
        mins = group.groupby('timestamp_min')
        for min, group_min in mins:
            num, blah = group_min.values.shape
            if num < 100:
                continue
            rtts = group_min['rtt'].apply(lambda x:x/1000.0).values
            # compute CDF here and save to figure?
            # OK :) i need netflix coupon
            to_plot.append([rtts,'LWAPP','r'])
            to_plot_lwapp.append([rtts,'LWAPP','r'])
            to_plot_clients[name].append([rtts,'LWAPP','r'])

    for k,val in to_plot_clients.items():
        print k,len(val)
        plot_cdf(val,'pdt_client_time_%s.png' % k,legend=False,xlogscale=True,
                 xlabel='PDT (ms)',ylabel='CDF',alpha=0.25,xlim=[0.1,10**5])

    plot_cdf(to_plot,'pdt_client_time',legend=True,xlogscale=True,
             xlabel='PDT (ms)',ylabel='CDF',alpha=0.1,xlim=[0.1,10**5])

    to_plot = []

    plot_cdf(to_plot,'pdt_client_time_percentiles',legend=False,xlogscale=True,
             xlabel='PDT (ms)',ylabel='CDF',alpha=0.25,xlim=[0.1,10**5])

    plot_cdf(to_plot_behop,'pdt_client_time_behop',legend=False,xlogscale=True,
             xlabel='PDT (ms)',ylabel='CDF',alpha=0.25,xlim=[0.1,10**5])

    plot_cdf(to_plot_lwapp,'pdt_client_time_lwapp',legend=False,xlogscale=True,
             xlabel='PDT (ms)',ylabel='CDF',alpha=0.25,xlim=[0.1,10**5])

    plot_cdf(to_plot_lwapp + to_plot_behop,'pdt_client_time_behop_lwapp',legend=False,xlogscale=True,
             xlabel='PDT (ms)',ylabel='CDF',alpha=0.25,xlim=[0.1,10**5])


files = args.files
df1 = pd.read_csv(files[0])
df1['timestamp_min'] = df1['timestamp'].apply(lambda x: int(x/60))
df1 = df1.drop(['tcp_seq','timestamp'],axis=1)

df2 = pd.read_csv(files[1])
df2['timestamp_min'] = df2['timestamp'].apply(lambda x: int(x/60))
df2 = df2.drop(['tcp_seq','timestamp'],axis=1)

rtt_client_time(df1,df2)
rtt_all(df1,df2)
