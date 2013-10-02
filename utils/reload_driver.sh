#!/bin/bash

rmmod ath9k_comon
rmmod ath9k_hw
rmmod ath
rmmod ath9k
rmmod mac80211
rmmod cfg80211

modprobe ath9k
