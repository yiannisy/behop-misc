#!/bin/bash
file=$1

#LOG=/var/log/cargus/pcap_to_argus.log
LOG=/tmp/pcap_to_argus.log

echo "Giving $file to Manu!"
echo "Giving $file to Manu!" >> $LOG

YY=`date +%Y`
mm=`date +%m`
dd=`date +%d`
HH=`date +%H`
MM=`date +%M`
#HHMM=$HH

PATH=/usr/local/bin:$PATH

##### for cargus
#PCAPF_TEST=~/tmp/cw_250_dec.pcap
PCAPF_TEST=$1
ARCHIVE=/var/log/cargus/archive
STATS=/var/log/cargus/stats
DIRIN=$ARCHIVE/$YY/$mm/$dd
if [ ! -d $DIRIN ]; then
  mkdir -p $DIRIN
fi
#PCAPF=$DIRIN/pcap.$YY.$mm.$dd.${HH}.00.00
#cp $PCAPF_TEST $PCAPF
#INPF=$DIRIN/pcap.$YY.$mm.$dd.$HHMM*
INPF=$PCAPF_TEST
ARGF=$DIRIN/argus.$YY.$mm.$dd.$HH.$MM.00

echo "Taking in pcap $INPF"
echo "Taking in pcap $INPF" >> $LOG
echo "Storing out $ARGF"
echo "Storing out $ARGF" >> $LOG

#http://comments.gmane.org/gmane.network.argus/8331
argus -F /dev/null -r $INPF -w $ARGF

echo "gzipping $ARGF to $ARGF.gz"
echo "gzipping $ARGF to $ARGF.gz" >> $LOG
gzip -f $ARGF
##### for cargus
