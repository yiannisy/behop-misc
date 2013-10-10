##
###!/bin/bash
sudo iw dev wlan0 interface add mon0 type monitor
ifconfig mon0 up
