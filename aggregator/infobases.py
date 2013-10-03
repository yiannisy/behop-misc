#import abc
from optparse import OptionParser
import inspect
import threading
import time
import abc
from conf import *
import copy
import math
import traceback
import collections
import itertools

def timing(f):
    def wrap(*args):
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        print '%s function took %0.3f ms' % (f.func_name, (time2-time1)*1000.0)
        return ret
    return wrap

#class InfoBase(threading.Thread):
class InfoBase:
    '''An information base implements queries on the running 
    window of an associated aggregator database..'''
    #object of the right subclass will be automatically attached 
    #to an aggregator when the aggregator is created.
    def __init__(self, feeds=None):
        #threading.Thread.__init__(self)
        #self.socket = None
        #self.running = True
	self.init_queries()

    def init_queries(self):
	ms = inspect.getmembers(self, predicate=inspect.ismethod)
	#for m in ms:
	#  print m
	ms = [m.split('query_')[1] for m,_ in ms if m.startswith('query_')]
	self.queries_provided = set(ms)

    def get_queries_provided(self):
      return list(self.queries_provided)

    def query(self, q):
      if q in self.queries_provided:
	res = getattr(self, 'query_' + q)(q)
	return 0, res
      else:
        print 'Bad query'
	res = getattr(self, 'query_unknown')(q)
	return 1, res

    def query_unknown(self):
      res = {'status':'UNKNOWN'}
      return res

    #def stop(self):
    #    self.running = False
    #        
    #def run(self):
    #    pass

class QueryWorker(threading.Thread):
  '''Class for dispatching a worker thread to maintain the result
  of a particular query at a certain refresh rate.'''
  def __init__(self, parentInfoBase, INTERVAL=DEF_QUERY_WORKER_INTERVAL):
    #super(QueryWorker, self).__init__(self)
    threading.Thread.__init__(self)
    self.ib = parentInfoBase
    self.agg = parentInfoBase.agg
    self.db = self.agg.db
    self.dblock = self.agg.dblock
    self.interval = INTERVAL
    self.running = False
    self.result = {}
    self.rlock = threading.RLock()
    self.setDaemon(True)

  def run(self):
    self.running = True
    while (self.running):
      with self.rlock:
	self.compute()
      time.sleep(self.interval)

  #@abc.abstractmethod
  #def qw_init(self):
  #  '''Write query worker's data initialization here.'''
  #  pass

  @abc.abstractmethod
  def compute(self):
    '''Write query worker's refresh computation here.'''
    pass

  #@abc.abstractmethod
  def get_result(self):
    #'''Write query worker's result return here.'''
    with self.rlock:
      return copy.deepcopy(self.result)

  def stop(self):
    self.running = False

class QW_snr_summary(QueryWorker):
  #def __init__(self, parentInfoBase, INTERVAL=DEF_QUERY_WORKER_INTERVAL):
  #  #super(QW_snr_summary, self).__init__(parentInfoBase, INTERVAL)
  #  QueryWorker.__init__(self, parentInfoBase, INTERVAL)
  #def qw_init(self):
  #  self.snr_summary = {}

  def linavg_dbsnrs(self, snrs):
    avg_snrs = {}
    for dst in snrs:
      avg_snrs[dst]= {}
      for apid in snrs[dst]:
        linsnrs = [math.pow(10, s/10.0) for s in snrs[dst][apid]]
	linavg = sum(linsnrs)/len(linsnrs)
	try:
	  #regular float
	  #avg_snrs[dst][apid] = (10.0 * math.log(linavg, 10), len(linsnrs))

	  #int with as many decimal places as indicated by the scaling factor
	  avg_snrs[dst][apid] = (int(10.0 * math.log(linavg, 10) * SNR_SCALING_FACTOR), len(linsnrs))
	except Exception as e:
	  print e
	  print '********* linavg = ', linavg
    return avg_snrs

  @timing
  def compute(self):
    print 'QW_snr_summary compute'
    #d={'ts':ts,'apid':apid,'link_id':link_id,'src_phy':src_phy,'seq':seq,'pkt_len':pkt_len,'snr':snr, 'type':ieee_type, 'subtype':ieee_subtype, 'tag':tag}
    #try:
    #  print self.db[-1]
    #except:
    #  pass

    snrs = {}
    #try:

    if not len(self.db):
      self.result = {}
      return

    ts_now = time.time()
    with self.dblock:
      idx = next((i for i, j in enumerate(self.db) if j['ts_rcv'] > ts_now - SNR_SUMMARY_INP_LOG_WINDOW_LEN_SECS), 0)
    print idx, len(self.db)
    db_slice = collections.deque(itertools.islice(self.db, idx, len(self.db)))

    #for d in self.db:
    for d in db_slice:
      #if d['tag'] != 'ACK_FR_AP':
      #  continue
      #dst = d['link_id'][3]
      #farid = dst

      if d['tag'] == 'DAT_TO_AP':
	ap,client,src,dst,bssid = d['link_id']
	farid = src


      elif d['tag'] == 'ACK_TO_AP':
	dst = d['link_id'][3]
	farid = dst	#note, this could also be another ap
	

      apid = d['apid']
      snr = d['snr']

      #convert to normalized form
      #apid = int(''.join(apid.split(':')), 16)
      #farid = int(''.join(farid.split(':')), 16)

      #apid = ''.join(apid.split(':'))
      #farid = ''.join(farid.split(':'))

      #apid = (''.join(apid.split(':'))).encode('ascii','ignore').lowercase
      #farid = (''.join(farid.split(':'))).encode('ascii','ignore').lowercase

      apid = ''.join(apid.split(':')).lower()
      farid = ''.join(farid.split(':')).lower()

      if farid not in snrs.keys():
	snrs[farid] = {}
      if apid not in snrs[farid].keys():
	snrs[farid][apid] = []
      snrs[farid][apid].append(snr)
    #except:
    #  print 'exception processing QW_snr_summary_compute'
    #  traceback.print_exc()
    #  traceback.print_tb()
    #  traceback.print_stack()

    #print snrs
    avg_snrs = self.linavg_dbsnrs(snrs)

    #print avg_snrs
    self.display_avg_snrs(avg_snrs)

    self.result = avg_snrs

    pass


  def display_avg_snrs(self,avg_snrs):
    for farid in avg_snrs:
      print 'farid=%s  ' % farid, 
      #print 'farid=%012x  ' % farid, 
      for apid in avg_snrs[farid]:
        snr, cnt = avg_snrs[farid][apid]
        #print 'apid=%s, snr=%6.2f, cnt=%5d' % (apid, snr, cnt), '|',
        print 'apid=%s, snr=%6.2f, cnt=%5d' % (apid, snr/SNR_SCALING_FACTOR, cnt), '|',
        #print 'apid=%012x, snr=%6.2f, cnt=%5d' % (apid, snr/SNR_SCALING_FACTOR, cnt), '|',
      print 

  #def result(self):
  #  return self.snr_summary

class PiInfoBase(InfoBase):


  def __init__(self, parentAgg):
    #super(PiInfoBase, self).__init__(self)
    InfoBase.__init__(self)
    self.agg = parentAgg
    #self.init_queries()
    self.qw_snr_summary = QW_snr_summary(self, 2)
    #self.qw_snr_summary.qw_init()
    #self.qw_snr_summary.run()
    self.qw_snr_summary.start()

  #def run(self):
    #while (self.running):
    #  #receive json query from socket
    #  #query = self.socket.recv_json()['query']

    #  #process query
    #  if query == 'snr_summary':
    #    res = snr_summary()
    #  else:
    #    res = unknown_query()

    #  #send json response
    #  #self.socket.send_json(res)
    #pass

  def query_snr_summary(self, q):
    #db = self.agg.db
    res = self.qw_snr_summary.get_result()
    res = {'status':'OK','res':res}
    return res

  def query_snrs_station(self, q):
    res = {'status':'OK'}
    return res

