
compute_bytes_log() {
    #------------------------------------
    #bytes sent and received by each host
    #------------------------------------

    #-------------
    # TCP
    #-------------
    #true uplink traffic is vlan tagged to vlan id 2000

    #source is a host, collapse all destinations ==> dstBytes are accurate download bytes
    rastrip -M -vlan -r ${INPF}* -w - | racluster -m saddr -s saddr daddr spkts dpkts sbytes dbytes -w - - src net 10.30.0.0/16 and tcp | rasort -m dbytes -s saddr daddr spkts dpkts sbytes dbytes | tr -s ' ' > /tmp/${PREFIX}t1_dstdown

    #source is a host, collapse all destinations, but only look at traffic that is vlan tagged ==> srcBytes are accurate upload bytes
    racluster -r ${INPF}* -m saddr -s saddr daddr spkts dpkts sbytes dbytes -w - - src net 10.30.0.0/16 and tcp and vid 2000 | rasort -m dbytes -s saddr daddr spkts dpkts sbytes dbytes | tr -s ' ' > /tmp/${PREFIX}t1_srcup


    #dest is a host, collapse all sources ==> srcBytes are accurate download bytes
    rastrip -M -vlan -r ${INPF}* -w - | racluster -m daddr -s saddr daddr spkts dpkts sbytes dbytes -w - - dst net 10.30.0.0/16 and tcp | rasort -m sbytes -s saddr daddr spkts dpkts sbytes dbytes | tr -s ' ' > /tmp/${PREFIX}t2_srcdown

    #dest is a host, collapse all sources, but only look at traffic that is vlan tagged ==> dstBytes are accurate upload bytes
    racluster -r ${INPF}* -m daddr -s saddr daddr spkts dpkts sbytes dbytes -w - - dst net 10.30.0.0/16 and tcp and vid 2000 | rasort -m sbytes -s saddr daddr spkts dpkts sbytes dbytes | tr -s ' ' > /tmp/${PREFIX}t2_dstup

    echo storing $BYTESF
    barguspy -l $LOC -c bytes_v --dstdown /tmp/${PREFIX}t1_dstdown --srcup /tmp/${PREFIX}t1_srcup --srcdown /tmp/${PREFIX}t2_srcdown --dstup /tmp/${PREFIX}t2_dstup -o $BYTESF -t $TS

    echo "location,@timestamp,client,in_pkts,out_pkts,in_bytes,out_bytes" > $BYTESF.upnonz
    grep -vE ",0$" $BYTESF >> $BYTESF.upnonz


    #-------------
    # UDP
    #-------------
    #source is a host, collapse all destinations ==> dstBytes are accurate download bytes
    rastrip -M -vlan -r ${INPF}* -w - | racluster -m saddr -s saddr daddr spkts dpkts sbytes dbytes -w - - src net 10.30.0.0/16 and udp | rasort -m dbytes -s saddr daddr spkts dpkts sbytes dbytes | tr -s ' ' > /tmp/${PREFIX}t1_dstdown_udp

    #source is a host, collapse all destinations, but only look at traffic that is vlan tagged ==> srcBytes are accurate upload bytes
    racluster -r ${INPF}* -m saddr -s saddr daddr spkts dpkts sbytes dbytes -w - - src net 10.30.0.0/16 and udp and vid 2000 | rasort -m dbytes -s saddr daddr spkts dpkts sbytes dbytes | tr -s ' ' > /tmp/${PREFIX}t1_srcup_udp


    #dest is a host, collapse all sources ==> srcBytes are accurate download bytes
    rastrip -M -vlan -r ${INPF}* -w - | racluster -m daddr -s saddr daddr spkts dpkts sbytes dbytes -w - - dst net 10.30.0.0/16 and udp | rasort -m sbytes -s saddr daddr spkts dpkts sbytes dbytes | tr -s ' ' > /tmp/${PREFIX}t2_srcdown_udp

    #dest is a host, collapse all sources, but only look at traffic that is vlan tagged ==> dstBytes are accurate upload bytes
    racluster -r ${INPF}* -m daddr -s saddr daddr spkts dpkts sbytes dbytes -w - - dst net 10.30.0.0/16 and udp and vid 2000 | rasort -m sbytes -s saddr daddr spkts dpkts sbytes dbytes | tr -s ' ' > /tmp/${PREFIX}t2_dstup_udp

    echo storing $BYTESF.udp
    barguspy -l $LOC -c bytes_v --dstdown /tmp/${PREFIX}t1_dstdown_udp --srcup /tmp/${PREFIX}t1_srcup_udp --srcdown /tmp/${PREFIX}t2_srcdown_udp --dstup /tmp/${PREFIX}t2_dstup_udp -o $BYTESF.udp -t $TS

    echo "location,@timestamp,client,in_pkts,out_pkts,in_bytes,out_bytes" > $BYTESF.udp.upnonz
    grep -vE ",0$" $BYTESF.udp >> $BYTESF.udp.upnonz
}

#------------------------------------
#bitrate sent and received by each host
#------------------------------------

compute_bitrate_log() {
    #bin size is the parameter in -M hard <bin size>
    #PRECISION=2
    PRECISION=0
    BIN_DUR=1m

    ##rastrip -M -vlan -r $INPF -w - | rabins -u -m saddr -M hard time $BIN_DUR -p$PRECISION -s stime saddr daddr sbytes dbytes sload dload - src net 10.30.0.0/16 and tcp | tr -s ' ' > /tmp/${PREFIX}t1
    ##rastrip -M -vlan -r $INPF -w - | rabins -u -m daddr -M hard time $BIN_DUR -p$PRECISION -s stime saddr daddr sbytes dbytes sload dload - dst net 10.30.0.0/16 and tcp | tr -s ' ' > /tmp/${PREFIX}t2


    #true uplink traffic is vlan tagged to vlan id 2000

    #source is a host, collapse all destinations ==> dstBytes are accurate download bytes
    rastrip -M -vlan -r ${INPF}* -w - | rabins -u -m saddr -M hard time $BIN_DUR -p$PRECISION -s stime saddr daddr sbytes dbytes sload dload - src net 10.30.0.0/16 and tcp | tr -s ' ' > /tmp/${PREFIX}avgrate_t1_dstdown

    #source is a host, collapse all destinations, but only look at traffic that is vlan tagged ==> srcBytes are accurate upload bytes
    rabins -u -r ${INPF}* -m saddr -M hard time $BIN_DUR -p$PRECISION -s stime saddr daddr sbytes dbytes sload dload - src net 10.30.0.0/16 and tcp and vid 2000 | tr -s ' ' > /tmp/${PREFIX}avgrate_t1_srcup


    #dest is a host, collapse all sources ==> srcBytes are accurate download bytes
    rastrip -M -vlan -r ${INPF}* -w - | rabins -u -m daddr -M hard time $BIN_DUR -p$PRECISION -s stime saddr daddr sbytes dbytes sload dload - dst net 10.30.0.0/16 and tcp | tr -s ' ' > /tmp/${PREFIX}avgrate_t2_srcdown

    #dest is a host, collapse all sources, but only look at traffic that is vlan tagged ==> dstBytes are accurate upload bytes
    rabins -u -r ${INPF}* -m daddr -M hard time $BIN_DUR -p$PRECISION -s stime saddr daddr sbytes dbytes sload dload - dst net 10.30.0.0/16 and tcp and vid 2000 | tr -s ' ' > /tmp/${PREFIX}avgrate_t2_dstup


    echo storing $AVGRATESF
    barguspy -l $LOC -c avgrates_v --dstdown /tmp/${PREFIX}avgrate_t1_dstdown --srcup /tmp/${PREFIX}avgrate_t1_srcup --srcdown /tmp/${PREFIX}avgrate_t2_srcdown --dstup /tmp/${PREFIX}avgrate_t2_dstup -o $AVGRATESF -t $TS

    ### create the filtered avgrates file
    echo "location,@timestamp,client,in_bytes,out_bytes,in_avgrate_bps,out_avgrate_bps" > $AVGRATESF.upnonz
    barguspy -l $LOC -c filter_IPs --reffile $BYTESF.upnonz --datafile $AVGRATESF -o $AVGRATESF.upnonz -a
}
