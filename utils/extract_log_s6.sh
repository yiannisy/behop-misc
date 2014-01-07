#/bin/bash

pcapfile=$1
pcapfile_out=anon_${pcapfile}
tmp_dir=.tmp_${pcapfile}
TCPTRACE_PATH=/home/yiannis/tcptrace-mod
YOUTUBE_REQUESTS_ALL=/home/yiannis/be-hop-misc/data/captures/youtube_requests_all.txt
NETFLIX_REQUESTS_ALL=/home/yiannis/be-hop-misc/data/captures/netflix_requests_all.txt
LOCATION=S6

mkdir ${tmp_dir}

mv $pcapfile ${tmp_dir}
# Remove udp-encapsulation
bittwiste -I ${tmp_dir}/$pcapfile -O ${tmp_dir}/studio6_out.pcap -D 15-90 

# Extract youtube/netflix requests before throwing-out content.
# We first need to strip out vlan tags for proper matching...
echo "Extracting youtube video requests..."
time ngrep "algorithm=throttle-factor" -t -I ${tmp_dir}/studio6_out.pcap -W byline | grep -v "#" | grep -E 'T 201|GET'  > ${tmp_dir}/youtube_requests.txt
echo "Extracting netflix video requests..."
time ngrep ".ismv/range" -t -I ${tmp_dir}/studio6_out.pcap -W byline | grep -v "#" | grep -E 'T 201|GET'  > ${tmp_dir}/netflix_requests.txt

# Analyze video requests
echo "Running video requests analysis..."
[ -e ${tmp_dir}/youtube_requests.txt ] && ./analyze_video_requests.py -s youtube -i ${tmp_dir}/youtube_requests.txt -o ${tmp_dir}/youtube.log
[ -e ${tmp_dir}/netflix_requests.txt ] && ./analyze_video_requests.py -s netflix -i ${tmp_dir}/netflix_requests.txt -o ${tmp_dir}/netflix.log

if [ -e ${tmp_dir}/netflix.log ]
then
    echo "location,timestamp,client,dest,bits,rate,dur,range,session_id" > ${tmp_dir}/netflix_db_s6.log
    sed -i -e 's/^/S6,/' ${tmp_dir}/netflix.log
    sed 's/\//-/g' ${tmp_dir}/netflix.log >> ${tmp_dir}/netflix_db_s6.log
    ./add_csv_to_db.sh ${tmp_dir}/netflix_db_s6.log logs.NetflixLog
fi

if [ -e ${tmp_dir}/youtube.log ]
then
    echo "location,timestamp,client,dest,bits,rate,dur,range" > ${tmp_dir}/youtube_db_s6.log
    sed -i -e 's/^/S6,/' ${tmp_dir}/youtube.log
    sed 's/\//-/g' ${tmp_dir}/youtube.log >> ${tmp_dir}/youtube_db_s6.log
    ./add_csv_to_db.sh ${tmp_dir}/youtube_db_s6.log logs.YoutubeLog
fi

rm -rf ${tmp_dir}
#rm -f ${tmp_dir}/${pcapfile}
echo "done with ${tmp_dir}"