import matplotlib
matplotlib.use('Agg')
import pylab
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pytz

def plot_cdf(lists,fname,legend=True,xlogscale=False,ylogscale=False,title='',xlim=[1,10**5],xlabel='',ylabel='',alpha=1):
    pylab.figure(figsize=(16,12))
    for l in lists:
        x = sorted(l[0])
        y = [float(i)/len(x) for i in range(len(x))]
        if len(l) == 3:
            c = l[2]
        else:
            c = 'g'
        pylab.plot(x,y,c,label=l[1],alpha=alpha,drawstyle='steps-post')
    pylab.grid(which="both")
    pylab.xlim(xlim)
    if legend:
        pylab.legend(loc=4)
    pylab.xlabel(xlabel)
    pylab.ylabel(ylabel)
    if xlogscale:
        pylab.xscale('log')
    pylab.title(title)
    pylab.savefig(fname)
