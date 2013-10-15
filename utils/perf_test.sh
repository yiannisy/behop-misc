#!/bin/bash
out_prefix=$1
out_tmp=".tmp_airport_output.txt"

os=`uname`

iperf -s -i 1 --reportstyle=C > ${out_prefix}_iperf.log &
echo date\|ping\|signal\|bssid\|channel\|mcs\|rate >> ${out_prefix}_wireless.log
if [ "$os" = "Darwin" ];
then
    echo "Running perf test for MacOSX"
    while true;
    do
	airport -I > ${out_tmp}
	date=`date`
	ping=`ping -c 1 -t 1 172.24.74.179 | grep time | awk -F' ' '{ print $7 }' | awk -F'=' '{print $2}'`
	bssid=`awk '/BSSID/' ${out_tmp} | awk -F': ' '{ print $2}'`
	rate=`awk '/lastTxRate/' ${out_tmp} | awk -F': ' '{ print $2}'`    
	channel=`awk '/channel/' ${out_tmp} | awk -F': ' '{ print $2}'`
	mcs=`awk '/MCS/' ${out_tmp} | awk -F': ' '{ print $2}'`
	signal=`awk '/agrCtlRSSI/' ${out_tmp} | awk -F': ' '{ print $2}'`
	echo ${date}\|${ping}\|${signal}\|${bssid}\|${channel}\|${mcs}\|${rate} >> ${out_prefix}_wireless.log
	sleep 1
    done
else
    echo "Running perf test for Linux"
    while true;
    do
	iwconfig wlan0 > ${out_tmp}
	date=`date`
	ping=`ping -c 1 -w 1 -W 1 172.24.74.179 | grep "time=" | awk -F' ' '{print $8}' | awk -F'=' '{print $2}'`
	bssid=`awk '/Access Point/' /tmp/out.txt | awk -F'Access Point: ' '{print $2}'`
	rate=`awk '/Bit Rate/' /tmp/out.txt | awk -F' ' '{print $2}' | awk -F '=' '{print $2}'`
	channel=`awk '/Frequency/' /tmp/out.txt | awk -F' ' '{print $2}' | awk -F ':' '{print $2}'`
	mcs=0
	signal=` awk '/Signal/' /tmp/out.txt | awk -F' ' '{print $4}' | awk -F '=' '{print $2}'`
	echo ${date}\|${ping}\|${signal}\|${bssid}\|${channel}\|${mcs}\|${rate} >> ${out_prefix}_wireless.log
	sleep 1
    done
fi

echo "done!"
killall iperf
