#/bin/bash

pcapfile=$1
pcapfile_out=anon_${pcapfile}
TCPTRACE_PATH=/home/yiannis/tcptrace-mod
YOUTUBE_REQUESTS_ALL=/home/yiannis/be-hop-misc/data/captures/youtube_requests_all.txt
NETFLIX_REQUESTS_ALL=/home/yiannis/be-hop-misc/data/captures/netflix_requests_all.txt

mkdir .tmp

# ANONYMIZING
# Split outgoing traffic and incoming traffic. Throw DNS traffic and content.
echo "Splitting in/out, removing DNS and content..."
time tcpdump -e -r ${pcapfile} -nnn "vlan and not port 53"  -w .tmp/studio5-out.pcap
time tcpdump -e -r ${pcapfile} -nnn "not vlan and not port 53" -w .tmp/studio5-in.pcap

# Extract youtube/netflix requests before throwing-out content.
# We first need to strip out vlan tags for proper matching...
echo "Stripping out vlan tags..."
tcprewrite --enet-vlan=del --infile=.tmp/studio5-out.pcap --outfile=.tmp/studio5-out_novlan.pcap
echo "Extracting youtube video requests..."
time ngrep "algorithm=throttle-factor" -t -I .tmp/studio5-out_novlan.pcap -W byline dst port 80 | grep -v "#" | grep -E 'T |GET'  > .tmp/youtube_requests.txt
echo "Extracting netflix video requests..."
time ngrep ".ismv/range" -t -I .tmp/studio5-out_novlan.pcap -W byline dst port 80 | grep -v "#" | grep -E 'T |GET'  > .tmp/netflix_requests.txt

# Anonymize incoming/outgoing traffic
echo "Anonymizing traffic..."
time tcprewrite -m 54 --mtu-trunc --srcipmap=0.0.0.0/0:192.0.0.0/8 --infile=.tmp/studio5-in.pcap --outfile=.tmp/studio5-in-anon.pcap
time tcprewrite -m 58 --mtu-trunc --dstipmap=0.0.0.0/0:192.0.0.0/8 --infile=.tmp/studio5-out.pcap --outfile=.tmp/studio5-out-anon.pcap
# Merge anonymized in/out pcaps.
echo "Merging in/out traffic..."
time mergecap -w .tmp/${pcapfile_out} .tmp/studio5-in-anon.pcap .tmp/studio5-out-anon.pcap

# ANALYSIS
# Analyze TCP flows for RTT.
echo "Running PDT analysis..."
cd .tmp
time ${TCPTRACE_PATH}/tcptrace -nnn -r -Z ${pcapfile_out} > tcptrace_summary.txt
cd ../ 
python analyze_tcptrace_sum.py

# Analyze video requests
echo "Running video requests analysis..."
[ -e .tmp/youtube_requests.txt ] && ./analyze_video_requests.py -s youtube -i .tmp/youtube_requests.txt -o .tmp/youtube.log
[ -e .tmp/netflix_requests.txt ] && ./analyze_video_requests.py -s netflix -i .tmp/netflix_requests.txt -o .tmp/netflix.log

# Store results
echo "Storing results..."
tar cvfz ${pcapfile_out}.tgz .tmp/${pcapfile_out}
mv ${pcapfile_out}.tgz ../data/captures/pcaps/
[ -e .tmp/youtube.log ] && cat .tmp/youtube.log >> ../data/captures/youtube.log
[ -e .tmp/netflix.log ] && cat .tmp/netflix.log >> ../data/captures/netflix.log
[ -e .tmp/youtube_requests.txt ] && cat .tmp/youtube_requests.txt >> ../data/captures/youtube_requests_all.log
[ -e .tmp/netflix_requests.txt ] && cat .tmp/netflix_requests.txt >> ../data/captures/netflix_requests_all.log
cd .tmp/
for i in rtt*.log;
do 
    [ -e $i ] && cat $i >> ../../data/captures/$i
done
cd ../
rm -rf .tmp
rm -f ${pcapfile}