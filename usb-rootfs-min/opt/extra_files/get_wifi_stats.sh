dpid=`ifconfig eth1 | grep HWaddr | tr -s ' ' | awk -F' ' '{print tolower($5)}' | sed -e 's/://g'`
for intf in wlan0 wlan1 mon0 mon1;
do
    rx_packets=`ifconfig ${intf} | grep "RX packets" | tr -s ' ' | awk -F[' :'] '{print $4}'`
    tx_packets=`ifconfig ${intf} | grep "TX packets" | tr -s ' ' | awk -F[' :'] '{print $4}'`
    rx_bytes=`ifconfig ${intf} | grep "bytes" | tr -s ' ' | awk -F[' :'] '{print $4}'`
    tx_bytes=`ifconfig ${intf} | grep "bytes" | tr -s ' ' | awk -F[' :'] '{print $9}'`
    echo $intf,$rx_packets,$tx_packets,$rx_bytes,$tx_bytes
done