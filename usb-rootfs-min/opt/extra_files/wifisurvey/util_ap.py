import sys
import socket
import binascii
import sys
from socket import ntohs
from subprocess import *
import string

import socket
import fcntl
import struct

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

def get_mac_address(intf):
    cmd = "ifconfig %s" % intf
    pipe = Popen(cmd,shell=True,stdout=PIPE)
    out,err = pipe.communicate()
    if (err):
        print "ifconfig failed - exiting...(%s)" % err
        sys.exit(0)
    else:
        line = string.split(out,"\n")[0]
        mac_addr = string.split(line.rstrip()," ")[-1]
        return mac_addr

#def get_hostname():
#    pipe = Popen("hostname",shell=True,stdout=PIPE)
#    out,err = pipe.communicate()
#    if (err):
#        print "hostname failed - exiting...(%s)" % err
#        sys.exit(0)
#    else:
#        hostname = out.lstrip().rstrip()
#        return hostname
