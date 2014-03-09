#!/bin/bash

intf=$1
prefix=$2

tcpdump -i ${intf} -nnn -s 1000 -w ${prefix}.%Y.%m%d-%H.%M.pcap -G 300 -Z yiannis -z ./extract_capwap_video.sh 'udp dst port 5247 and udp[14:2] & 0xfff8 = 0x00'