#!/bin/bash

#file=test1.pcap
file=$1
#tmp_dir=.tmp_capwap_${file}
#mkdir $tmp_dir
#mv $file ${tmp_dir}/
#cd $tmp_dir

#date=`date +%Y.%m.%d-%H.%M`

# filter first frame packets only
tcpdump -nnn -r ${file} 'udp[14:2] & 0xfff8 = 0x00' -w dl_f0.pcap
# Filter packets with capwap.header.length=2 and remove CAPWAP and WiFi crap
tcpdump -nnn -r dl_f0.pcap 'udp[9:1] & 0xf8 = 0x10 and udp[17:1] = 0x08' -w test_l2.pcap
bittwiste -I test_l2.pcap -O test_l2_data.pcap -D 1-68
# Filter packets with capwap.header.length=4 and remove CAPWAP and WiFi crap
tcpdump -nnn -r dl_f0.pcap 'udp[9:1] & 0xf8 = 0x20 and udp[25:1] = 0x08' -w test_l4.pcap
bittwiste -I test_l4.pcap -O test_l4_data.pcap -D 1-76

# Create a unified pcap file
mergecap test_l2_data.pcap test_l4_data.pcap -w test_data.pcap

