#!/usr/bin/env python
from plot_defaults import *
from IPython import embed

df1 = pd.read_csv('behop.out',sep='\t')
df2 = pd.read_csv('lwapp.out',sep='\t')
df1.columns = ['rebuffers','duration','bitrate','account_id','session_id']
df2.columns = ['rebuffers','duration','bitrate','account_id','session_id']

# Only sessions > 60 secs.
behop = df1[df1['rebuffers'] > -1]
behop = behop[behop['duration'] > 60]
lwapp = df2[df2['rebuffers'] > -1]
lwapp = lwapp[lwapp['duration'] > 60]

# Bitrate
to_plot = []
to_plot.append([behop['bitrate'],'BeHop','g'])
to_plot.append([lwapp['bitrate'],'LWAPP','r'])

plot_cdf(to_plot,'netflix_metric_bitrate',legend=True,xlogscale=False,
         xlabel='Average Session Bitrate',ylabel='CDF',xlim=[0.1,5000])

# Rebuffers
plt.figure()
plt.hist([behop['rebuffers'],lwapp['rebuffers']],color=['g','r'],label=['BeHop','LWAPP'])
plt.xlabel('Rebuffers')
plt.ylabel('Number of Sessions')
plt.xticks([0,1,2])
plt.legend()
plt.savefig('netflix_metric_rebuffers.png')

# Summary
print "BeHop samples : %d" % behop.count()['bitrate']
print "LWAPP samples : %d" % lwapp.count()['bitrate']
