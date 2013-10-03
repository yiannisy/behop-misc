import SocketServer
import json
import threading
import socket


class QueryHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        try:
            data = json.loads(self.request.recv(1024).strip())
            # process the data, i.e. print it:
            print data
            # send some 'ok' back
            #self.request.sendall(json.dumps({'return':'ok'}))
        except Exception, e:
            print "Exception while receiving query: ", e

	try:
	  q = data['query']
        except Exception, e:
            print "Exception while parsing query: ", e
	    res = {'status':'exc_parsing_query'}
	    self.request.sendall(json.dumps(res))
	    return

	qp = self.server.query_provider
	if q not in qp:
	  print 'No query provider for query %s' % q
	  res = {'status':'unhandled_query'}
	  self.request.sendall(json.dumps(res))
	else:
	  try:
	    p = qp[q]
	  except Exception, e:
	    print 'Exception processing query %s' % q
	    res = {'status':'exc_processing_query'}
	    self.request.sendall(json.dumps(res))
	    return

	  status, res = p.query(q)
	  if status != 0:
	    print 'Error processing query %s' % q
	    res = {'status':'err_processing_query'}
	    self.request.sendall(json.dumps(res))
	    return

	  #send successful response
	  self.request.sendall(json.dumps(res))


class QueryServer_(SocketServer.ThreadingTCPServer):
    allow_reuse_address = True

    def set_query_provider(self, qp):
      self.query_provider = qp

class QueryServer(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    port = QUERY_HANDLER_LOCAL_PORT
    print 'Initializing query server'
    self.query_provider = {}
    self.server = QueryServer_(('127.0.0.1', port), QueryHandler)
    self.server.set_query_provider(self.query_provider)
  
  def register_query_provider(self, provider, query_list):
    for q in query_list:
      if q in self.query_provider.keys():
        print "Provider for query %s is already registered, skipping" % q
      else:
        print "Provider for query %s registered" % q
	self.query_provider[q] = provider

  def run(self):
    print 'Starting query server'
    self.server.serve_forever()

  def stop(self):
    print 'Stopping query server'
    self.server.shutdown()


class QueryClient():
  #DEF_QUERY = {'message':'hello world!', 'test':123.4}
  DEF_QUERY = {'query':'snrs_station', 'station_id':'000000000001'}

  def __init__(self):
    self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.s.connect(('127.0.0.1', QUERY_HANDLER_LOCAL_PORT))

  def query(self, query=DEF_QUERY):
    self.s.send(json.dumps(query))
    result = json.loads(self.s.recv(1024))
    print result

  def close(self):
    self.s.close()

def testQuery():
  qc = QueryClient()
  qc.query()
  qc.close()

if __name__ == '__main__':
    testQuery()
