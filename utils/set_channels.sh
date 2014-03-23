#!/bin/bash

if [ $# -lt 2 ]
then
	echo "Usage : $0 alloc_type (520,540,220) channel_allocation_file"
	exit
fi

type=$1
fname=$2

case "$type" in
520)
	echo "Setting a 5GHz/20MHz channel allocation"
	offset=2
	;;
540)
	echo "Setting a 5GHz/40MHz channel allocation"
	offset=3
	;;
220)
	echo "Setting a 2.4GHz/20MHz channel allocation"
	offset=4
	;;
*)
	echo "Invalid channel allocation type."
	exit
	;;
esac

while read p;do
    studio=`echo $p|awk -F',' '{print $1}'`
    case "$offset" in
    2)
	    channel=`echo $p|awk -F',' '{print $2}'`
	    radio="radio1"
	    ;;
    3)
	    channel=`echo $p|awk -F',' '{print $3}'`
	    radio="radio1"
	    ;;
    4)
	    channel=`echo $p|awk -F',' '{print $4}'`
	    radio="radio0"
	    ;;
    esac
    echo "Setting channel $channel at studio $studio"
    ./pssh_script root@studio5-$studio-pi.sunet "uci set wireless.${radio}.channel=$channel;uci commit"
done < $fname
exit



