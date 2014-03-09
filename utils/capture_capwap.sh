#!/bin/bash

intf=$1
prefix=$2

tcpdump -i ${intf} -nnn -s 150 -w ${prefix}.%Y.%m%d-%H.%M.pcap -G 300 -z ./extract_capwap.sh 'udp port 5247 and udp[14:2] & 0xfff8 = 0x00'