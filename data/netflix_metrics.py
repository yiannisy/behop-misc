#!/usr/bin/env python
from plot_defaults import *
from IPython import embed

behop = pd.read_csv('behop.out',sep='\t')
lwapp = pd.read_csv('lwapp.out',sep='\t')
behop.columns = ['rebuffers','duration','bitrate','account_id','session_id']
lwapp.columns = ['rebuffers','duration','bitrate','account_id','session_id']

print "BeHop Orig samples : %d" % behop.count()['bitrate']
print "LWAPP Orig samples : %d" % lwapp.count()['bitrate']

# Only sessions > 60 secs.
behop = behop[behop['rebuffers'] > -1]
lwapp = lwapp[lwapp['rebuffers'] > -1]
print "BeHop Started samples : %d" % behop.count()['bitrate']
print "LWAPP Started samples : %d" % lwapp.count()['bitrate']

behop = behop[behop['duration'] > 60]
lwapp = lwapp[lwapp['duration'] > 60]
print "BeHop > 1 min samples : %d" % behop.count()['bitrate']
print "LWAPP > 1 min samples : %d" % lwapp.count()['bitrate']

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
