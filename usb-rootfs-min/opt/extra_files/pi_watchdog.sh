tries=0
while [[ $tries -lt 10 ]]
do
    if ping -c 1 8.8.8.8 >/dev/null
    then
	exit 0
    fi
    tries=$((tries+1))
done
date=`date`
echo "watchdog rebooted at $date" >> /opt/reboot.log
/sbin/reboot -f
