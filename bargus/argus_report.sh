#!/bin/bash

N_ARGS=4
if [ $# -ne "$N_ARGS" ]
then
    YY=`date +%Y`
    MM=`date +%m`
    DD=`date +%d`
    HH=`date +%H`
else
    YY=$1
    MM=$2
    DD=$3
    HH=$4
fi


/usr/local/bin/bargus $YY $MM $DD $HH >> /var/log/argus/bargus.log 
/usr/local/bin/bargus_to_db.sh $YY $MM $DD $HH >> /var/log/argus/bargus_to_db.log
/usr/local/bin/cargus  $YY $MM $DD $HH >> /var/log/argus/cargus.log
/usr/local/bin/cargus_to_db.sh $YY $MM $DD $HH >> /var/log/argus/cargus_to_db.log
