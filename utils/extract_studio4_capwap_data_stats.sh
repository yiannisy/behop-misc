#!/bin/bash

N_ARGS=4
f_out="/tmp/cargus_out.txt"

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

day="$YY.$MM.$DD-$HH:59:00"
date_prefix=$YY.$MM.$DD.$HH
cd /var/log/cargus/archive/$YY/$MM/$DD/
rabins -r *${date_prefix}* -M 60m hard -m saddr - ipv4 and tcp and src net 10.30.0.0/16 -w - | rasort -r - -m saddr -s saddr dpkts spkts dbytes sbytes | tr -s ' ' > ${f_out}
sed -i '/SrcAddr/d' ${f_out}
sed -i 's/^ *//g' ${f_out}
sed -i "s/^/${day},/g" ${f_out}
sed -i 's/ /,/g' ${f_out}
sed -i "s/^/S4,/g" ${f_out}
sed -i "1ilocation,@timestamp,client,in_pkts,out_pkts,in_bytes,out_bytes" ${f_out}
cd -
./add_csv_to_db_direct.sh ${f_out} logs_transferlog
rm ${f_out}