#!/bin/bash
BASE_DIR='/home/yiannis/behop-pox-s5'
UTIL_DIR='/home/yiannis/be-hop-misc/utils'
DASHBOARD_DIR='/home/yiannis/behop_dashboard'
CURDIR=`pwd`

cd $BASE_DIR
now=`date +%Y.%m.%d-%H.%M`
new_log=pox.$now.log
cp pox.log ${new_log}
echo '' > pox.log

cp ${new_log} /tmp/.pox.log
mv ${new_log} logs/
echo "date|msg|label|dpid|addr|channel|band|snr" > /tmp/.probes.log
cat /tmp/.pox.log | grep LTSTA | grep PROBE_REQ >> /tmp/.probes.log
cat /tmp/.pox.log | grep LTSTA | grep ASSOC_REQ > /tmp/.assocs.log

cd $UTIL_DIR
./update_node_db.py

cd /tmp/
cat .pox.log | grep FSM > fsm.log
sed -i 's/ : /|/g' fsm.log
sed -i 's/| /|/g' fsm.log
sed -i 's/ (/|/g' fsm.log
sed -i 's/)/|/g' fsm.log
sed -i 's/, /|/g' fsm.log
sed -i 's/ProbeReq,/ProbeReq|/g' fsm.log
cat fsm.log | grep -E "> ASSOC|ASSOC -> NONE" | grep -v Probe | awk -F'|' '{ print $1 "|" $3 "|" $4 "|" $5}' > events.log
cat fsm.log | grep -E "SNIFF -> RESERVED" | awk -F'|' '{ print $1 "|" $3 "|" $4 "|" $5}' >> events.log
sed -i 's/,/./g' events.log
sed -i 's/|/,/g' events.log
sed -i '1itimestamp,client,event_name,signal' events.log

cat .pox.log | grep PROBE_REQ | awk -F'|' '{ print $5 "," $7 }' | sort | uniq > detected.txt
d=`date +"%Y-%m-%d %H:%M:%S%z,"`;sed -i "s/^/$d/g" detected.txt
sed -i "s/^/DETECTED,PROBEREQ,Monitor,/g" detected.txt
sed -i '1ievent_name,event_signal,category,timestamp,client,band' detected.txt

cd $DASHBOARD_DIR
python manage.py csvimport --mappings='' --model='logs.EventLog' /tmp/events.log
python manage.py csvimport --mappings='' --model='logs.EventLog' /tmp/detected.txt

cd $CURDIR