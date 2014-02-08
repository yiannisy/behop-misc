#!/bin/bash

intf=$1
prefix=$2

sudo tcpdump -i ${intf} -nnn -s 250 -w ${prefix}.%Y.%m%d-%H.%M.pcap -G 300 -Z yiannis -z ./extract_capwap_s4.sh 'udp port 5247 and udp[14:2] & 0xfff8 = 0x00'