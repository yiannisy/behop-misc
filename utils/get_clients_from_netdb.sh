#!/bin/bash
in_fname=$1
out_fname=$2
tmp=.tmpwhois.txt

while read p;do 
    whois -h whois.stanford.edu $p > $tmp
    if grep -Fq "rescomp" $tmp
    then
	hwaddr=`cat $tmp | grep $p -B 1 | grep hw-addr | awk -F' ' '{ print $3 }' | sed -e 's/^ *//g' -e 's/ *$//g' -e 's/\.//g'`
	cpu=`cat $tmp | grep cpu | awk -F':' '{ print $2 }' | sed -e 's/^ *//g' -e 's/ *$//g'`
	os=`cat $tmp | grep op-sys | awk -F':' '{ print $2 }' | sed -e 's/^ *//g' -e 's/ *$//g'`
	echo "S6",$p,$hwaddr,$cpu,$os,"unknown","0,0" >> $out_fname
    fi
done < $1
sed -i '1ilocation,ip_address,mac_address,type,os,user,bands_2GHz,bands_5GHz' $out_fname