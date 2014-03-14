date=`date +%Y.%m.%d-%H:%M:%S`
dpid=`ifconfig eth1 2> /dev/null | grep HWaddr | tr -s ' ' | awk -F' ' '{print tolower($5)}' | sed -e 's/://g'`

for intf in wlan0 wlan1 mon0 mon1;
do
    rx_packets=`ifconfig ${intf} 2> /dev/null | grep "RX packets" | tr -s ' ' | awk -F[' :'] '{print $4}'`
    tx_packets=`ifconfig ${intf} 2> /dev/null | grep "TX packets" | tr -s ' ' | awk -F[' :'] '{print $4}'`
    rx_bytes=`ifconfig ${intf} 2> /dev/null | grep "bytes" | tr -s ' ' | awk -F[' :'] '{print $4}'`
    tx_bytes=`ifconfig ${intf} 2> /dev/null | grep "bytes" | tr -s ' ' | awk -F[' :'] '{print $9}'`
    if [[ -z "$rx_packets" ]];then rx_packets=0;fi
    if [[ -z "$tx_packets" ]];then tx_packets=0;fi
    if [[ -z "$rx_bytes" ]];then rx_bytes=0;fi
    if [[ -z "$tx_bytes" ]];then tx_bytes=0;fi
	
    echo $date,$dpid,$intf,$rx_packets,$tx_packets,$rx_bytes,$tx_bytes >> /var/run/cur_wifistats.log
done
sed -i 's/,,/,0,/g' /var/run/cur_wifistats.log
sed -i 's/,,/,0,/g' /var/run/cur_wifistats.log
echo 'timestamp,dpid,intf,rx_pkts,tx_pkts,rx_bytes,tx_bytes' > /var/run/wifistats.log
/opt/utils/wifisurvey/calculate_wifi_stats.py >> /var/run/wifistats.log 
/opt/utils/ap_import.py /var/run/wifistats.log logs_wifiintflog
mv /var/run/cur_wifistats.log /var/run/last_wifistats.log
rm /var/run/wifistats.log