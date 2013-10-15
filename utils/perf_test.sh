#!/bin/bash
out_prefix=$1
out_tmp=".tmp_airport_output.txt"

iperf -s -i 1 --reportstyle=C > ${out_prefix}_iperf.log &

echo date\|ping\|signal\|bssid\|channel\|mcs\|rate >> ${out_prefix}_wireless.log
while true;
do
    airport -I > ${out_tmp}
    date=`date`
    ping=`ping -c 1 -t 1 thetida.stanford.edu | grep time | awk -F' ' '{ print $7 }' | awk -F'=' '{print $2}'`
    bssid=`awk '/BSSID/' ${out_tmp} | awk -F': ' '{ print $2}'`
    rate=`awk '/lastTxRate/' ${out_tmp} | awk -F': ' '{ print $2}'`    
    channel=`awk '/channel/' ${out_tmp} | awk -F': ' '{ print $2}'`
    mcs=`awk '/MCS/' ${out_tmp} | awk -F': ' '{ print $2}'`
    signal=`awk '/agrCtlRSSI/' ${out_tmp} | awk -F': ' '{ print $2}'`
    echo ${date}\|${ping}\|${signal}\|${bssid}\|${channel}\|${mcs}\|${rate} >> ${out_prefix}_wireless.log
    sleep 1
done

echo "done!"
killall iperf
