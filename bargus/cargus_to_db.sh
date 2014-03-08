#!/bin/bash
LOGF=/home/manub/be-hop-misc/bargus/cargus_to_db.log
echo `date`": this is cargus to db, over" >> $LOGF

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

PATH=/usr/local/bin:$PATH

ARCHIVE=/var/log/cargus/archive
DIRIN=$ARCHIVE/$YY/$MM/$DD
INPF=$DIRIN/argus.$YY.$MM.$DD.$HH

echo processing $INPF
bname=`basename $INPF`

STATS=/var/log/cargus/stats
DIROUT=$STATS/$YY/$MM/$DD
BYTESF=$DIROUT/bytes.$bname.csv
AVGRATESF=$DIROUT/avgrates.$bname.csv
TS="malakas.$YY.$MM.$DD.$HH.59.00"

bargus_to_db_django(){
/home/manub/be-hop-misc/utils/add_csv_to_db.sh $BYTESF.upnonz logs.TransferLog
/home/manub/be-hop-misc/utils/add_csv_to_db.sh $AVGRATESF.upnonz logs.BandwidthLog
}

bargus_to_db_direct(){
/home/manub/be-hop-misc/utils/add_csv_to_db_direct.sh $BYTESF.upnonz logs_transferlog
#/home/manub/be-hop-misc/utils/add_csv_to_db_direct.sh $AVGRATESF.upnonz logs_bandwidthlog
}

#eval `ssh-agent`
#pidval=${SSH_AGENT_PID}
#ssh-add /home/manub/.ssh/manub-mg-xen

#bargus_to_db_django
bargus_to_db_direct

#kill ${pidval}


#  done
#done
