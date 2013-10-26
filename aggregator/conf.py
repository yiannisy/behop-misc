import os, sys

PROXY_PUBLISHER = 5586
PROXY_SUBSCRIBER = 5587
UDP_PORT_PROD = 5588				#aggregator port
UDP_PORT_TEST = 5589				#aggregator port

#QUERY_HANDLER_LOCAL_PORT = 5589		
QUERY_TCP_SERVER_IP = "172.24.74.179"
#QUERY_TCP_SERVER_PORT = 5589		
#QUERY_TCP_SERVER_PORT = 5590
QUERY_TCP_SERVER_PORT = 9935	#yiannis' controller

SNR_ALERT_THRESHOLD = 25

POLL_INTERVAL = 5

UPWARD_PORT = 'eth0'

UDP_IP = "172.24.74.179"

#DEF_AGG_FILTER="(type data or (type ctl and subtype ack))"
DEF_AGG_FILTER="(type data or (type ctl and subtype ack)) or "

DEF_QUERY_WORKER_INTERVAL = 1		#default interval in secs at which a query worker
					#refreshes its statistics 

SNR_SUMMARY_INP_LOG_WINDOW_LEN_SECS = 10

#SNR_SCALING_FACTOR = 100.0	#for retaining two decimal places in serialization
SNR_SCALING_FACTOR = 1.0


#QUERY_STDOUT_QUIET = False 
QUERY_STDOUT_QUIET = True

#COLLECTOR_MODEL = 'pycollector'
COLLECTOR_MODEL = 'ccollector'


#-------------------------------------------------------------------------------------
# DO NOT EDIT AFTER THIS
#-------------------------------------------------------------------------------------
if QUERY_STDOUT_QUIET:
  #quiet
  QUERY_STDOUT = open(os.devnull,"w")
else:
  #regular output
  QUERY_STDOUT = sys.stdout

