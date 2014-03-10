#!/bin/bash

S4_IP="128.12.164.253"
S6_ip="128.12.172.253"

file=$1
tmp_dir=.tmp_capwap_${file}
file_out=data.pcap
mkdir $tmp_dir
mv $file ${tmp_dir}/
cd $tmp_dir

ipaddr=`ifconfig eth0 | grep "inet addr" | tr -s ' ' | awk -F'[ :]' '{print $4}'`
echo "Running at $ipaddr"
if [[ "$ipaddr" == "$S4_IP" ]]
then
    LOC='S4'
elif [[ $"ipaddr" == "$S6_IP" ]]
then 
    LOC='S6'
else
    echo "No location variable set---quitting."
    exit
fi
echo "Extacting CAPWAP for ${LOC}"

date=`date +%Y.%m.%d-%H.%M`
start_date=`date +%H.%M.%S`


../extract_capwap_data.sh $file $file_out

# Extract youtube/netflix requests before throwing-out content.
echo "Extracting youtube video requests..."
time ngrep "\/videoplayback" -t -I $file_out -W byline dst port 80 | grep -v "#" | grep -E 'T |GET'  > youtube_requests.txt

echo "Extracting netflix video requests..."
time ngrep ".ismv|isma|.aac|.ts.prdy" -t -I $file_out -W byline dst port 80 | grep -v "#" | grep -E 'T |GET'  > netflix_requests.txt

# Store requests locally
echo "Storing results..."
[ -e youtube_requests.txt ] && cat youtube_requests.txt >> ../../data/captures/youtube_requests_all_${LOC}.log
[ -e netflix_requests.txt ] && cat netflix_requests.txt >> ../../data/captures/netflix_requests_all_${LOC}.log

cd ../
rm -rf ${tmp_dir}
rm -f ${pcapfile}
echo "done with ${tmp_dir}"
end_date=`date +%H.%M.%S`
echo "START: ${start_date} END: ${end_date}" >> studio4_video_processing.log
