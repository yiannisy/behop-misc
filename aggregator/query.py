import socket
from conf import *
import threading
import time
import sys
import json
import time

BUFFER_SIZE = 1024

class QueryHandler():
    def __init__(self, qc):
	self.qTCPClient = qc

    def handle(self, query):
        try:
            data = json.loads(query)
            # process the data, i.e. print it:
            print data
            # send some 'ok' back
            #self.request.sendall(json.dumps({'return':'ok'}))
        except Exception, e:
            print "Exception while deserializing query: ", e
	    res = {'status':'exc_deserializing_query'}
	    return res

	try:
	  q = data['query']
        except Exception, e:
            print "Exception while parsing query: ", e
	    res = {'status':'exc_parsing_query'}
	    return res

	#qp = self.server.query_provider
	qp = self.qTCPClient.query_provider
	if q not in qp:
	  print 'No query provider for query %s' % q
	  res = {'status':'unhandled_query'}
	else:
	  try:
	    p = qp[q]
	  except Exception, e:
	    print 'Exception processing query %s' % q
	    res = {'status':'exc_processing_query'}
	    return res

	  status, res = p.query(q)
	  if status != 0:
	    print 'Error processing query %s' % q
	    res = {'status':'err_processing_query'}
	    return res

	  #indicate the query that we are responding to
	  res['query'] = q

	  #send successful response
	  return res



class QueryTCPClient(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    self.running = False
    self.s = None
    self.query_provider = {}
    self.channel = 'MON_IB'
    #self.server = QueryServer_(('127.0.0.1', port), QueryHandler)
    #self.server.set_query_provider(self.query_provider)
    self.query_handler = QueryHandler(self)
    self.setDaemon(True)

  def set_query_provider(self, qp):
    self.query_provider = qp

  
  def register_query_provider(self, provider, query_list):
    for q in query_list:
      if q in self.query_provider.keys():
        print "Provider for query %s is already registered, skipping" % q
      else:
        print "Provider for query %s registered" % q
	self.query_provider[q] = provider

  def connect(self):
      while(True):
          print "Attempting to connect to %s:%d" % (QUERY_TCP_SERVER_IP, QUERY_TCP_SERVER_PORT)
          self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          try:
              self.s.connect((QUERY_TCP_SERVER_IP, QUERY_TCP_SERVER_PORT))
              break
          except Exception as e:
              # failed to connect - retry after 1 sec
              self.s.close()
              time.sleep(1)
      # send a hello message to the controller upon connection.
      self.send_channel({'query':'echo-req'})

  def reconnect(self):
      print "Connection to the controller closed - reconnecting..."
      self.s.close()
      self.connect()

  def send_channel(self, msg):
      '''
      Sends a message to the channel we are connected.
      '''
      msg['CHANNEL'] = self.channel
      self.s.send(json.dumps(msg))

  def run(self):
    print 'Query TCP client connecting to server'
    self.connect()
    print "Connected to the Controller"
    print 'Query TCP client starting query handler'
    self.running = True
    while self.running:
      try:
          query = self.s.recv(BUFFER_SIZE)
      except:
          self.reconnect()
      if query == '':
          self.reconnect()
      else:
          query = query.strip()
      #MESSAGE = "Hello, World!"
      #self.s.send(MESSAGE)
      print 'Query handler received query: %s' % query

      res = self.query_handler.handle(query)
      print 'Query handler returned response: %s' % res

      print 'Sending back response'
      try:
          self.send_channel(res)
      except:
          self.reconnect()
  def stop(self):
    self.running = False
    self.s.close()



class QueryTCPServer(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    self.running = False
    self.s = None
    self.conn = None
    pass

  def run(self):
    self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.s.bind((QUERY_TCP_SERVER_IP, QUERY_TCP_SERVER_PORT))
    print 'Query server waiting for connection'
    self.s.listen(1)

    self.conn, addr = self.s.accept()
    print 'Query handler tcp client connected from:', addr

    self.running = True
    while self.running:
	##send query - for testing
	#time.sleep(8)
	#query = {'query':'snr_summary'}
	#print 'Sending query %s' % query
	#self.conn.send(json.dumps(query))
	#time.sleep(2)

	##receive response
	#resp = self.conn.recv(BUFFER_SIZE).strip()
	#resp = json.loads(resp)
	#print resp


	#send query
	query = raw_input('query? >> ')
	query = eval(query)
	print 'Sending query %s' % query
	self.conn.send(json.dumps(query))

	#receive response
	resp = self.conn.recv(BUFFER_SIZE).strip()
	resp = json.loads(resp)
	print resp

  def stop(self):
    self.running = False
    self.s.close()

def testQueryServer():
  qs = QueryTCPServer()
  try:
    qs.run()
  except Exception as e:
    print "Exception while receiving query: ", e
    qs.stop()

def testQueryClient():
  qc = QueryTCPClient()
  try:
    qc.run()
  except KeyboardInterrupt as e:
    print "Exception while receiving query: ", e
    qc.stop()

if __name__ == '__main__':
    if sys.argv[1] == 'sv':
      testQueryServer()
    if sys.argv[1] == 'cl':
      testQueryClient()
