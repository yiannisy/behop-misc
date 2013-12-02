#/bin/bash

pcapfile=$1
pcapfile_out=/tmp/anon_studio5.pcap
TCPTRACE_PATH=/home/yiannis/tcptrace-mod/

# ANONYMIZING
# Split outgoing traffic and incoming traffic. Throw DNS traffic and content.
echo "Splitting in/out, removing DNS and content..."
time tcpdump -e -r ${pcapfile} -nnn "vlan and not port 53"  -w /tmp/studio5-out.pcap
time tcpdump -e -r ${pcapfile} -nnn "not vlan and not port 53" -w /tmp/studio5-in.pcap

# Extract youtube/netflix requests before throwing-out content.
echo "Extracting youtube video requests..."
time ngrep "algorithm=throttle-factor" -I /tmp/studio5-out.pcap -W byline dst port 80 | grep -v "#" | grep -E 'T 201|GET'  > youtube_requests.txt
echo "Extracting netflix video requests..."
time ngrep ".ismv/range" -I /tmp/studio5-out.pcap -W byline dst port 80 | grep -v "#" | grep -E 'T 201|GET'  > netflix_requests.txt

# Anonymize incoming/outgoing traffic
echo "Anonymizing traffic..."
time tcprewrite -m 54 --mtu-trunc --srcipmap=0.0.0.0/0:192.0.0.0/8 --infile=/tmp/studio5-in.pcap --outfile=/tmp/studio5-in-anon.pcap
time tcprewrite -m 58 --mtu-trunc --dstipmap=0.0.0.0/0:192.0.0.0/8 --infile=/tmp/studio5-out.pcap --outfile=/tmp/studio5-out-anon.pcap
# Merge anonymized in/out pcaps.
echo "Merging in/out traffic..."
time mergecap -w ${pcapfile_out} /tmp/studio5-in-anon.pcap /tmp/studio5-out-anon.pcap

# ANALYSIS
# Get youtube/netflix requests
# Analyze TCP flows for RTT.
echo "Running PDT analysis..."
mkdir .tmp
cd .tmp
time ${TCPTRACE_PATH}tcptrace -nnn -r -Z ../${pcapfile_out} > tcptrace_summary.txt
cd ../ ; python analyze_tcptrace_sum.py; rm -rf .tmp

# Analyze video requests
echo "Running video requests analysis..."
python analyze_video_requests.py