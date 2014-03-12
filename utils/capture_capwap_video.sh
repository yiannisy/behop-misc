#!/bin/bash

intf=$1
prefix=$2

lwapp_ap_prefix="172.19.159"
pcap_expr="host 172.19.159.20"

for i in {21..45};do
    pcap_expr="$pcap_expr or host $lwapp_ap_prefix.$i"
done
pcap_expr="( $pcap_expr )"
echo $pcap_expr

tcpdump -i ${intf} -nnn -s 1000 -w ${prefix}.%Y.%m%d-%H.%M.pcap -G 300 -z ./extract_capwap_video.sh "udp dst port 5247 and udp[14:2] & 0xfff8 = 0x00 and $pcap_expr"