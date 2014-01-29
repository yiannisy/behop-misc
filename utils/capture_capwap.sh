#!/bin/bash

sudo tcpdump -i eth1 -nnn -s 150 -w studio6.%Y.%m%d-%H.%M.pcap -G 900 -Z yiannis -z ./extract_capwap.sh 'udp port 5247 and udp[14:2] & 0xfff8 = 0x00'