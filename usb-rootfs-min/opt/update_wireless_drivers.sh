opkg update
echo "Removing existing modules"
opkg remove kmod-mac80211 --force-removal-of-dependent-packages
echo "Installing new modules"
opkg install kmod-ath9k
echo "Wireless drivers update---reboot for changes to apply!"