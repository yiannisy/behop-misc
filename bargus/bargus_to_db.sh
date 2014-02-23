#!/bin/bash
LOGF=/home/manub/be-hop-misc/bargus/bargus_to_db.log
echo `date`": this is bargus to db, over" >> $LOGF

YY=`date +%Y`
mm=`date +%m`
dd=`date +%d`
HH=`date +%H`
MM=`date +%M`
M=${MM:0:1}	#0'th character
HHMM=$HH.$M


#YY=2014
#mm=02
#dates="1 10"
#YY=2013
#mm=12
#dates="23 31"
#dd=03
#HH=01
#for dd in `seq -w $dates`; do
#  for HH in `seq -w 0 23`; do
    HHMM=$HH.$M

PATH=/usr/local/bin:$PATH

#/var/log/argus/archive/2013/12/15
ARCHIVE=/var/log/argus/archive
DIRIN=$ARCHIVE/$YY/$mm/$dd
INPF=$DIRIN/argus.$YY.$mm.$dd.$HHMM*.gz


if [ ! -e $INPF ]; then
  echo Input file $INPF not found, continuing...
  continue
fi


echo processing $INPF
bname=`basename $INPF .gz`

STATS=/var/log/argus/stats
DIROUT=$STATS/$YY/$mm/$dd
BYTESF=$DIROUT/bytes.$bname.csv
AVGRATESF=$DIROUT/avgrates.$bname.csv
TS=$bname


bargus_to_db_django(){
/home/manub/be-hop-misc/utils/add_csv_to_db.sh $BYTESF.upnonz logs.TransferLog
/home/manub/be-hop-misc/utils/add_csv_to_db.sh $AVGRATESF.upnonz logs.BandwidthLog
}

bargus_to_db_direct(){
/home/manub/be-hop-misc/utils/add_csv_to_db_direct.sh $BYTESF.upnonz logs_transferlog
/home/manub/be-hop-misc/utils/add_csv_to_db_direct.sh $AVGRATESF.upnonz logs_bandwidthlog
}

eval `ssh-agent`
pidval=${SSH_AGENT_PID}
ssh-add /home/manub/.ssh/manub-mg-xen

#bargus_to_db_django
bargus_to_db_direct

kill ${pidval}


#  done
#done
