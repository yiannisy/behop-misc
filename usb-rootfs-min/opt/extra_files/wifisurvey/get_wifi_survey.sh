date=`date +%Y.%m.%d-%H:%M:%S`
dpid=`ifconfig eth1 2> /dev/null | grep HWaddr | tr -s ' ' | awk -F' ' '{print tolower($5)}' | sed -e 's/://g'`

for intf in wlan0 wlan1;
do
    vals=`cat /var/run/wifi-survey-${intf} 2> /dev/null | awk -F[',:'] '{print $4 "," $6 "," $8 "," $10 "," $12 }'`
    echo $date,$dpid,$intf,$vals >> /var/run/wifisurvey.log
done
sed -i 's/,,/,0,/g' /var/run/wifisurvey.log
sed -i 's/,,/,0,/g' /var/run/wifisurvey.log
sed -i '1itimestamp,dpid,intf,freq,active,busy,receive,transmit' /var/run/wifisurvey.log
/opt/utils/ap_import.py /var/run/wifisurvey.log logs_channelutillog
rm /var/run/wifisurvey.log
