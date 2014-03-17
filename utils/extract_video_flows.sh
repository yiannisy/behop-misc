#/bin/bash

pcapfile=$1
pcapfile_out=studio5_anon_${pcapfile}
tmp_dir=.tmp_${pcapfile}
TCPTRACE_PATH=/home/yiannis/tcptrace-mod
YOUTUBE_REQUESTS_ALL=/home/yiannis/be-hop-misc/data/captures/youtube_requests_all.txt
NETFLIX_REQUESTS_ALL=/home/yiannis/be-hop-misc/data/captures/netflix_requests_all.txt
LOCATION=S5

mkdir ${tmp_dir}
start_date=`date +%H.%M.%S`

# ANONYMIZING
# Split outgoing traffic and incoming traffic. Throw DNS traffic and content.
echo "Splitting in/out, removing DNS and content..."
time tcpdump -e -r ${pcapfile} -nnn "vlan and not port 53"  -w ${tmp_dir}/studio5-out.pcap

# Extract youtube/netflix requests before throwing-out content.
# We first need to strip out vlan tags for proper matching...
echo "Stripping out vlan tags..."
tcprewrite --enet-vlan=del --infile=${tmp_dir}/studio5-out.pcap --outfile=${tmp_dir}/studio5-out_novlan.pcap
echo "Extracting youtube video requests..."
time ngrep "\/videoplayback" -t -I ${tmp_dir}/studio5-out_novlan.pcap -W byline dst port 80 | grep -v "#" | grep -E 'T |GET'  > ${tmp_dir}/youtube_requests.txt

echo "Extracting netflix video requests..."
time ngrep "ismv|isma|\.ts\.prdy|\.aac" -t -I ${tmp_dir}/studio5-out_novlan.pcap -W byline dst port 80 | grep -v "#" | grep -E 'T |GET'  > ${tmp_dir}/netflix_requests.txt


# Analyze video requests
echo "Running video requests analysis..."
[ -e ${tmp_dir}/youtube_requests.txt ] && ./analyze_video_requests.py -s youtube -i ${tmp_dir}/youtube_requests.txt -o ${tmp_dir}/youtube.log
[ -e ${tmp_dir}/netflix_requests.txt ] && ./analyze_video_requests.py -s netflix -i ${tmp_dir}/netflix_requests.txt -o ${tmp_dir}/netflix.log

# Store results locally
echo "Storing results..."
#tar cvfz ${pcapfile_out}.tgz ${tmp_dir}/${pcapfile_out}
#mv ${pcapfile_out}.tgz ../data/captures/pcaps/
[ -e ${tmp_dir}/youtube.log ] && cat ${tmp_dir}/youtube.log >> ../data/captures/youtube.log
[ -e ${tmp_dir}/netflix.log ] && cat ${tmp_dir}/netflix.log >> ../data/captures/netflix.log
[ -e ${tmp_dir}/youtube_requests.txt ] && cat ${tmp_dir}/youtube_requests.txt >> ../data/captures/youtube_requests_all.log
[ -e ${tmp_dir}/netflix_requests.txt ] && cat ${tmp_dir}/netflix_requests.txt >> ../data/captures/netflix_requests_all.log

# Add sums to the db.
if [ -e ${tmp_dir}/netflix.log ]
then
    echo "location,timestamp,client,dest,bits,rate,dur,range,session_id" > ${tmp_dir}/netflix_db.log
    sed -i -e 's/^/S5,/' ${tmp_dir}/netflix.log
    sed 's/\//-/g' ${tmp_dir}/netflix.log >> ${tmp_dir}/netflix_db.log
    #add_csv_to_db.sh ${tmp_dir}/netflix_db.log logs.NetflixLog
fi

if [ -e ${tmp_dir}/youtube.log ]
then
    echo "location,timestamp,client,dest,bits,rate,dur,range" > ${tmp_dir}/youtube_db.log
    sed -i -e 's/^/S5,/' ${tmp_dir}/youtube.log
    sed 's/\//-/g' ${tmp_dir}/youtube.log >> ${tmp_dir}/youtube_db.log
    #add_csv_to_db.sh ${tmp_dir}/youtube_db.log logs.YoutubeLog
fi

# Split outgoing traffic and incoming traffic. Throw DNS traffic and content.
echo "Splitting in/out, removing DNS and content..."
time tcpdump -e -r ${pcapfile} -nnn "not vlan and not port 53" -w ${tmp_dir}/studio5-in.pcap
# Anonymize incoming/outgoing traffic
echo "Anonymizing traffic..."
time tcprewrite --srcipmap=0.0.0.0/0:192.0.0.0/8 --infile=${tmp_dir}/studio5-in.pcap --outfile=${tmp_dir}/studio5-in-anon.pcap
time tcprewrite --dstipmap=0.0.0.0/0:192.0.0.0/8 --infile=${tmp_dir}/studio5-out_novlan.pcap --outfile=${tmp_dir}/studio5-out-anon.pcap
# Merge anonymized in/out pcaps.
echo "Merging in/out traffic..."
time mergecap -w ${tmp_dir}/studio5-anon.pcap ${tmp_dir}/studio5-in-anon.pcap ${tmp_dir}/studio5-out-anon.pcap
#bittwiste -I ${tmp_dir}/studio5-anon.pcap -O ${tmp_dir}/${pcapfile_out} -D 54-9999
editcap -s 60 ${tmp_dir}/studio5-anon.pcap ${tmp_dir}/${pcapfile_out}
mv ${tmp_dir}/${pcapfile_out} ../data/rtt-analysis/

rm -rf ${tmp_dir}
rm -f ${pcapfile}
echo "done with ${tmp_dir}"
end_date=`date +%H.%M.%S`
echo "START: ${start_date} END: ${end_date}" >> studio5_processing.log
