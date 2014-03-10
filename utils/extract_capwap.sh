#!/bin/bash


S4_IP="128.12.164.253"
S6_IP="128.12.172.253"

file=$1
tmp_dir=.tmp_capwap_${file}
mkdir $tmp_dir
mv $file ${tmp_dir}/
cd $tmp_dir

date=`date +%Y.%m.%d-%H.%M`
start_date=`date +%H.%M.%S`

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
echo "Extacting CAPWAP for ${LOC}"


# Downlink traffic
# Get only downlink traffic.
tcpdump -r $file -nnn udp src port 5247 -w dl_f0.pcap
# Keep only first fragment packets
#tcpdump -nnn -r dl.pcap 'udp[14:2] & 0xfff8 = 0x00' -w dl_f0.pcap
# Filter packets with capwap.header.length=2 and remove CAPWAP tunnel
tcpdump -nnn -r dl_f0.pcap 'udp[9:1] & 0xf8 = 0x10 and udp[17:1] & 0x0f = 0' -w dl_l2.pcap
#tcpdump -nnn -r dl_f0.pcap 'udp[9:1] & 0xf8 = 0x10' -w dl_l2.pcap
bittwiste -I dl_l2.pcap -O dl_l2_mon.pcap -D 1-50 -M 105
# Filter packets with capwap.header.length=4 and remove CAPWAP tunnel
tcpdump -nnn -r dl_f0.pcap 'udp[9:1] & 0xf8 = 0x20 and udp[25:1] & 0x0f = 0' -w dl_l4.pcap
#tcpdump -nnn -r dl_f0.pcap 'udp[9:1] & 0xf8 = 0x20' -w dl_l4.pcap
bittwiste -I dl_l4.pcap -O dl_l4_mon.pcap -D 1-58 -M 105

# Create a unified pcap file
mergecap dl_l2_mon.pcap dl_l4_mon.pcap -w dl_mon.pcap

tcpdump -tt -nnn -r dl_mon.pcap -e wlan[1] = 0x10 | awk -F' ' '{print $1 "," $2 "," $3 ",ASSOC_RESP"}' >> events.txt
tcpdump -tt -nnn -r dl_mon.pcap -e wlan[1] = 0x30 | awk -F' ' '{print $1 "," $2 "," $3 ",REASSOC_RESP"}' >> events.txt
#tcpdump -tt -nnn -r dl_mon.pcap -e wlan[1] = 0x50 | awk -F' ' '{print $1 "," $2 "," $3 ",PROBE_RESP"}' >> events.txt
tcpdump -tt -nnn -r dl_mon.pcap -e wlan[1] = 0xa0 | awk -F' ' '{print $1 "," $2 "," $3 ",DISASSOC"}' >> events.txt
tcpdump -tt -nnn -r dl_mon.pcap -e wlan[1] = 0xc0 | awk -F' ' '{print $1 "," $2 "," $3 ",DEAUTH"}' >> events.txt


# Uplink traffic
# Get only uplink traffic.
tcpdump -r $file -nnn udp dst port 5247 -w ul_f0.pcap
# Keep only first fragment packets
#tcpdump -nnn -r ul.pcap 'udp[14:2] & 0xfff8 = 0x00' -w ul_f0.pcap
# Filter packets with capwap.header.length=2 and remove CAPWAP tunnel
tcpdump -nnn -r ul_f0.pcap 'udp[9:1] & 0xf8 = 0x10 and udp[17:1] & 0x0f = 0' -w ul_l2.pcap
#tcpdump -nnn -r ul_f0.pcap 'udp[9:1] & 0xf8 = 0x10' -w ul_l2.pcap
bittwiste -I ul_l2.pcap -O ul_l2_mon.pcap -D 1-50 -M 105
# Filter packets with capwap.header.length=4 and remove CAPWAP tunnel
tcpdump -nnn -r ul_f0.pcap 'udp[9:1] & 0xf8 = 0x20 and udp[25:1] & 0x0f = 0' -w ul_l4.pcap
#tcpdump -nnn -r ul_f0.pcap 'udp[9:1] & 0xf8 = 0x20' -w ul_l4.pcap
bittwiste -I ul_l4.pcap -O ul_l4_mon.pcap -D 1-58 -M 105

# Create a unified pcap file
mergecap ul_l2_mon.pcap ul_l4_mon.pcap -w ul_mon.pcap

tcpdump -tt -nnn -r ul_mon.pcap -e wlan[1] = 0x00 | awk -F' ' '{print $1 "," $2 "," $4 ",ASSOC_REQ"}' >> events.txt
tcpdump -tt -nnn -r ul_mon.pcap -e wlan[1] = 0x20 | awk -F' ' '{print $1 "," $2 "," $4 ",REASSOC_REQ"}' >> events.txt
#tcpdump -tt -nnn -r ul_mon.pcap -e wlan[1] = 0x40 | awk -F' ' '{print $1 "," $2 "," $4 ",PROBE_REQ"}' >> events.txt
tcpdump -tt -nnn -r ul_mon.pcap -e wlan[1] = 0xa0 | awk -F' ' '{print $1 "," $2 "," $4 ",DISASSOC"}' >> events.txt
tcpdump -tt -nnn -r ul_mon.pcap -e wlan[1] = 0xc0 | awk -F' ' '{print $1 "," $2 "," $4 ",DEAUTH"}' >> events.txt
#tcpdump -tt -nnn -r ul_mon.pcap -e wlan[1] = 0x80 | awk -F' ' '{print $1 "," $2 "," $4 ",BEACON"}' >> events.txt

cat events.txt | sort -n > _events.txt; 
sed -i 's/DA:/DA!/g' _events.txt
sed -i 's/BSSID:/BSSID!/g' _events.txt
sed -i 's/SA:/SA!/g' _events.txt
sed -i 's/://g' _events.txt
awk -F'[,!]' '$2=="BSSID" {print $1 "," $5 "," $3 "," $6}' _events.txt > events_${LOC}.txt
awk -F'[,!]' '$4=="BSSID" {print $1 "," $3 "," $5 "," $6}' _events.txt >> events_${LOC}.txt

sed -i "s/^/${LOC},/g" events_${LOC}.txt

cat events_${LOC}.txt | while read line ; do 
ts=`echo $line | awk -F',' '{ print $2 }'`
d=`date -d @${ts} +"%Y-%m-%d %H:%M:%S"`
new_line=`echo $line | awk -F',' '{ print $1 "," $3 "," $4 "," $5 ",unknown,WiFi,0"}'`  #"," $3 "," $4 "," $5 }'
echo $d,$new_line >> _events_${LOC}.txt
done
sed -i '1i@timestamp,location,client,dpid,event_signal,event_name,category,band' _events_${LOC}.txt
add_csv_to_db_direct.sh _events_${LOC}.txt logs_eventlog

outfile=capwap_data.pcap
../extract_capwap_data.sh $file $outfile
pcap_to_argus.sh $outfile

cd ../
rm -rf ${tmp_dir}

end_date=`date +%H.%M.%S`
echo "START : ${start_date} | END : ${end_date}" >> studio4_processing.log