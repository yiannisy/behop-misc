#!/usr/bin/env python

from plot_defaults import *
import pandas as pd
import numpy as np
from IPython import embed
parser = argparse.ArgumentParser(description="Plotting script.")
parser.add_argument('--files',default=None,nargs='+',help='files to read rtts from')
parser.add_argument('--labels',default=None,nargs='+',help='label for each file')
args = parser.parse_args()
names = []
all_colors = ['c-.','b--','g-','r-.']

osx = ['10.30.68.111','10.30.68.126','10.30.68.136','10.30.84','10.30.69.140','10.30.69.17',
       '10.30.69.196','10.30.69.20','10.30.69.25','10.30.69.34','10.30.70.14','10.30.70.15','10.30.73.136',
       '10.30.68.130','10.30.68.150','10.30.69.222','10.30.69.241','10.30.71.201']
ios = ['10.30.68.151','10.30.68.232','10.30.68.30','10.30.68.51','10.30.68.53','10.30.68.88','10.30.69.107',
       '10.30.69.11','10.30.69.138','10.30.69.147','10.30.69.224','10.30.69.41','10.30.69.65','10.30.70.22','10.30.73.137','10.30.73.139','10.30.70.152']
android = ['10.30.69.153','10.30.71.184','10.30.72.215']
windows =['10.30.69.191','10.30.69.232']

def rtt_all(dfs,labels):
    to_plot = []
    colors = all_colors[0:len(labels)]
    for df,label,color in zip(dfs,labels,colors):                                        
        rtts = df['rtt'].apply(lambda x:x/1000.0).astype('float32').values
        to_plot.append([rtts,label,color])
        
    plot_cdf(to_plot,'pdt_all_log.pdf',legend=True,xlogscale=True,
             xlabel='Packet Delivery Time (ms)',ylabel='CDF',xlim=[1,10**3])

    plot_cdf(to_plot,'pdt_all_lin.pdf',legend=True,xlogscale=False,
             xlabel='Packet Delivery Time (ms)',ylabel='CDF',alpha=0.5,xlim=[0,300])


def rtt_client(dfs,labels):
    to_plot = []
    to_plot_clients = defaultdict(list)
    colors = all_colors[0:len(labels)]

    for df,label,color in zip(dfs,labels,colors):
        g = df.groupby('ip')
        for name, group in g:
            rtts = group['rtt'].apply(lambda x:x/1000.0).values
            if len(rtts) < 1000:
                print "too few samples for %s" % name
                continue
            # compute CDF here and save to figure?
            # OK :) i need netflix coupon
            to_plot.append([rtts,label,color])
            to_plot_clients[name].append([rtts,label,color])

    plot_cdf(to_plot,'pdt_client_log',legend=False,xlogscale=True,
             xlabel='Packet Delivery Time (ms)',ylabel='CDF',alpha=0.1,xlim=[0.01,10**4])

    plot_cdf(to_plot,'pdt_client_lin',legend=False,xlogscale=False,
             xlabel='Packet Delivery Time (ms)',ylabel='CDF',alpha=0.1,xlim=[0,300])


    for k,val in to_plot_clients.items():
        print k,len(val)
        plot_cdf(val,'pdt_client_%s_log.pdf' % k,legend=False,xlogscale=True,
                 xlabel='PDT (ms)',ylabel='CDF',xlim=[0.1,10**4])

        plot_cdf(val,'pdt_client_%s_lin.pdf' % k,legend=False,xlogscale=True,
                 xlabel='PDT (ms)',ylabel='CDF',xlim=[0,400])



def rtt_client_time(df1,df2):
    to_plot_behop = []
    to_plot_lwapp = []
    to_plot = []
    to_plot_clients = defaultdict(list)
    to_plot_os = defaultdict(list)

    g = df1.groupby('ip')
    for name, group in g:
        #if name not in osx:
        #    continue
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
        plot_cdf(val,'pdt_client_time_%s.pdf' % k,legend=False,xlogscale=True,
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
if args.labels:
    labels = args.labels
else:
    labels = ["A","B","C","D","E","F","G"]
    labels = labels[0:len(files)]
dfs = []

for file in files:
    df1 = pd.read_csv(file,dtype={'timestamp': np.float32,'rtt':np.float32,'tcp_seq':np.int32,'ip':np.str})
    df1['timestamp_min'] = df1['timestamp'].apply(lambda x: int(x/60))
    df1 = df1.drop(['tcp_seq','timestamp'],axis=1)
    dfs.append(df1)
    
#rtt_client_time(df1,df2)
#rtt_client(dfs,labels)
rtt_all(dfs,labels)

embed()
