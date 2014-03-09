#/bin/bash

file=$1
tmp_dir=.tmp_capwap_${file}
file_out=data.pcap
LOC=S4
mkdir $tmp_dir
mv $file ${tmp_dir}/
cd $tmp_dir

date=`date +%Y.%m.%d-%H.%M`
start_date=`date +%H.%M.%S`


../extract_capwap_data_s4.sh $file $file_out

# Extract youtube/netflix requests before throwing-out content.
echo "Extracting youtube video requests..."
time ngrep "videoplayback\?clen" -t -I $file_out -W byline dst port 80 | grep -v "#" | grep -E 'T |GET'  > youtube_requests.txt

echo "Extracting netflix video requests..."
time ngrep ".ismv/range" -t -I $file_out -W byline dst port 80 | grep -v "#" | grep -E 'T |GET'  > netflix_requests.txt

# Store requests locally
echo "Storing results..."
[ -e youtube_requests.txt ] && cat youtube_requests.txt >> ../../data/captures/youtube_requests_all_${LOC}.log
[ -e netflix_requests.txt ] && cat netflix_requests.txt >> ../../data/captures/netflix_requests_all_${LOC}.log

cd ../
#rm -rf ${tmp_dir}
#rm -f ${pcapfile}
echo "done with ${tmp_dir}"
end_date=`date +%H.%M.%S`
echo "START: ${start_date} END: ${end_date}" >> studio4_video_processing.log
