#!/bin/bash

date=`date +%Y.%m.%d-%H.%M`
fname1=/tmp/load_survey_5.${date}.txt
fname2=/tmp/load_survey_2.${date}.txt
#echo ${fname}

#ssh-agent /bin/bash
#ssh-add

#eval `ssh-agent -s` 

rm -rf /tmp/pssh-out/*
./pi_pssh.sh pi-load.txt "cat /var/run/wifi-survey-wlan1" > /dev/null
grep -R active /tmp/pssh-out/ | awk -F'/' '{print $4}' > /tmp/load.txt
mv /tmp/load.txt ${fname1}


rm -rf /tmp/pssh-out/*
./pi_pssh.sh pi-load.txt "cat /var/run/wifi-survey-wlan0" > /dev/null
grep -R active /tmp/pssh-out/ | awk -F'/' '{print $4}' > /tmp/load.txt
mv /tmp/load.txt ${fname2}

#kill $SSH_AGENT_PID