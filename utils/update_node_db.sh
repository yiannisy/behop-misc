#!/bin/bash
BASE_DIR='/home/yiannis/behop-pox-s5'
UTIL_DIR='/home/yiannis/be-hop-misc/utils'
CURDIR=`pwd`

cd $BASE_DIR
now=`date +%Y.%m.%d-%H.%M`
new_log=pox.$now.log
cp pox.log ${new_log}
echo '' > pox.log

cp ${new_log} /tmp/.pox.log
echo "date|msg|label|dpid|addr|channel|band" > /tmp/.probes.log
cat /tmp/.pox.log | grep LTSTA | grep PROBE_REQ >> /tmp/.probes.log
cat /tmp/.pox.log | grep LTSTA | grep ASSOC_REQ > /tmp/.assocs.log

cd $UTIL_DIR
./update_node_db.py

cd $CURDIR