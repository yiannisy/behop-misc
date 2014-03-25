from matplotlib import rc, rcParams


DEF_AXIS_LEFT = 0.18
DEF_AXIS_RIGHT = 0.95
DEF_AXIS_BOTTOM = 0.1
DEF_AXIS_TOP = 0.99
DEF_AXIS_WIDTH = DEF_AXIS_RIGHT - DEF_AXIS_LEFT
DEF_AXIS_HEIGHT = DEF_AXIS_TOP - DEF_AXIS_BOTTOM
# add_axes takes [left, bottom, width, height]
DEF_AXES = [DEF_AXIS_LEFT, DEF_AXIS_BOTTOM, DEF_AXIS_WIDTH, DEF_AXIS_HEIGHT]

AXIS_2Y_RIGHT = 0.8
AXIS_2Y_WIDTH = AXIS_2Y_RIGHT - DEF_AXIS_LEFT
AXES_2Y = [DEF_AXIS_LEFT, DEF_AXIS_BOTTOM, AXIS_2Y_WIDTH, DEF_AXIS_HEIGHT]

AXES_LABELSIZE = 24
TICK_LABELSIZE = 24
TEXT_LABELSIZE = 24

COLOR_LIGHTGRAY = '#cccccc'

#COLOR_HLINES = '#606060'
COLOR_HLINES = 'black'
HLINE_LABELSIZE = 24
HLINE_LINEWIDTH = 2

rc('axes', **{'labelsize' : 'large',
              'titlesize' : 'large',
              'grid' : True})
rc('legend', **{'fontsize': 'xx-large'})
rcParams['axes.labelsize'] = AXES_LABELSIZE
rcParams['xtick.labelsize'] = TICK_LABELSIZE
rcParams['ytick.labelsize'] = TICK_LABELSIZE
rcParams['xtick.major.pad'] = 4
rcParams['ytick.major.pad'] = 6
rcParams['figure.subplot.bottom'] = DEF_AXIS_LEFT
rcParams['figure.subplot.left'] = DEF_AXIS_LEFT
rcParams['figure.subplot.right'] = DEF_AXIS_RIGHT
rcParams['lines.linewidth'] = 2
#rcParams['grid.color'] = COLOR_LIGHTGRAY
rcParams['grid.linewidth'] = 1.0

rcParams['ps.useafm'] = True
rcParams['pdf.use14corefonts'] = True
#rcParams['text.usetex'] = True
#rcParams['text.latex.preamble'] = r'\usepackage{amsmath}'

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pytz
from matplotlib import cm
import argparse
import numpy as np
import pandas as pd
from operator import itemgetter
from collections import defaultdict
import random
import time
import string,sys,os

def plot_cdf(lists,fname,legend=True,xlogscale=False,ylogscale=False,title='',xlim=[1,10**5],xlabel='',ylabel='',alpha=1):
    plt.figure(figsize=(16,12))
    for l in lists:
        x = sorted(l[0])
        # sample down in case we have too many data. Keep up to 10000 points to print.
        # matplotlib crashes with memoryerror when we put too many data...
        orig_len = len(x)
        if len(x) > 10000:
            sampling_rate = len(x)/10000
        else:
            sampling_rate = 1
        x = [x[i] for i in range(0,len(x),max(1,sampling_rate))]
        print "sampling down from %d samples to %d" % (orig_len, len(x))
        y = [float(i)/len(x) for i in range(len(x))]
        if len(l) == 3:
            c = l[2]
        else:
            c = 'g'
        plt.plot(x,y,c,label=l[1],alpha=alpha,drawstyle='steps-post')
    plt.grid()
    plt.xlim(xlim)
    if legend:
        plt.legend(loc=4)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    if xlogscale:
        plt.xscale('log')
    plt.title(title)
    plt.savefig(fname)
