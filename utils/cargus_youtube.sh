#/bin/bash

N_ARGS=4

S4_IP="128.12.164.253"
S6_IP="128.12.172.253"

PATH=/usr/local/bin:/sbin:$PATH

ipaddr=`ifconfig eth0 | grep "inet addr" | tr -s ' ' | awk -F'[ :]' '{print $4}'`
echo "Running at $ipaddr"
if [[ "$ipaddr" == "$S4_IP" ]]
then
    LOC='S4'
elif [[ "$ipaddr" == "$S6_IP" ]]
then 
    LOC='S6'
else
    echo "No location variable set---quitting."
    exit
fi
echo "Extacting CAPWAP video for ${LOC}"


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


ARGUS_PREFIX=/var/log/cargus/archive
day=$YY.$MM.$DD
date="$YY/$MM/$DD"
date_hour="$YY/$MM/$DD $HH"
ARGUS_DIR=$ARGUS_PREFIX/$date
UTIL_DIR=/home/yiannis/be-hop-misc/utils/


# Get all the youtube flows for this day.
cat /home/yiannis/be-hop-misc/data/captures/youtube_requests_all_${LOC}.log | grep "$date_hour" | awk -F'[ :]' '{ print $6,$9 }' | sort | uniq -c | sort -n > /tmp/youtube_flows_${LOC}.txt

my_pcap_expr="host 172.24.74.179"
cd $ARGUS_DIR
echo "#################"
echo "Processing Youtube for $YY-$MM-$DD ($LOC)"
while read p;do
    host_src=`echo $p | awk -F' ' '{ print $2 }'`
    #port_src=`echo $p | awk -F' ' '{ print $3 }'`
    host_dst=`echo $p | awk -F' ' '{ print $3 }'`
    pcap_expr="$my_pcap_expr or (host $host_src and host $host_dst)"
    my_pcap_expr=$pcap_expr
done < /tmp/youtube_flows_${LOC}.txt

if [[ -z "$pcap_expr" ]]
then
    echo "no youtube flow detected."
    exit
else
    echo "processing argus data for $pcap_expr"
fi
fname=/tmp/youtube_${day}_${LOC}.txt
rabins -r argus.$YY.$MM.$DD.$HH.* -M 1m hard -m saddr daddr - $pcap_expr -w - | rasort -r - -m stime -s stime saddr daddr sload dload srate drate | tr -s ' ' > ${fname}
cp ${fname} ${fname}.orig
sed -i '/StartTime/d' ${fname}
sed -i 's/^ *//g' ${fname}
sed -i "s/^/${day}-/g" ${fname}
sed -i "s/^/${LOC},/g" ${fname}
#sed -i '/-23:5/d' ${fname}
sed -i 's/ /,/g' ${fname}
sed -i 's/*//g' ${fname}
sed -i 's/\.,/,/g' ${fname}
sed -i 's/\.$//g' ${fname}
lines=`cat ${fname} | wc -l`
thres=3
if [ "$lines" -gt "$thres" ];then
    echo "kai twra edw"
    sed -i "1d" ${fname}
	#sed -i "${lines}d" ${fname}
    sed -i '1ilocation,@timestamp,client,target,bitrate_up,bitrate_down,packetrate_up,packetrate_down' ${fname}
    cd ${UTIL_DIR}/
    add_csv_to_db_direct.sh ${fname} logs_youtubebitratelog
    cd -
fi
