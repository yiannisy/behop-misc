#!/bin/bash
while read p;do
    echo $p
    ping -c 1 -w 5 $p
done < pi-load.txt
