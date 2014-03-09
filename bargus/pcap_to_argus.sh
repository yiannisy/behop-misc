#!/bin/bash
file=$1

#LOG=/var/log/cargus/pcap_to_argus.log
LOG=/tmp/pcap_to_argus.log

echo "Giving $file to Manu!"
echo "Giving $file to Manu!" >> $LOG

N_ARGS=4

if [ $# -ne "$N_ARGS" ]
then
    YY=`date +%Y`
    MM=`date +%m`
    DD=`date +%d`
    HH=`date +%H`
    mm=`date +%M`
else
    YY=$1
    MM=$2
    DD=$3
    HH=$4
fi

PATH=/usr/local/bin:$PATH

##### for cargus
PCAPF_TEST=$1
ARCHIVE=/var/log/cargus/archive
STATS=/var/log/cargus/stats
DIRIN=$ARCHIVE/$YY/$MM/$DD
if [ ! -d $DIRIN ]; then
  mkdir -p $DIRIN
fi

INPF=$PCAPF_TEST
ARGF=$DIRIN/argus.$YY.$MM.$DD.$HH.$mm.00

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
