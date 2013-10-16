echo `date` ":"  "Mounting usb drive..."
./pi_pssh.sh -t 10 "mount /dev/sda1 /mnt/"
echo `date` ":"  "Cleanin-up USB drive."
./pi_pssh.sh -t 10 "rm -rf /mnt/*"
echo `date` ":"  "Copying usb image over..."
./pi_pscp.sh -r -t 20 ../usb-rootfs-min/* /mnt/
echo `date` ":"  "Unmounting usb drive..."
./pi_pssh.sh -t 10 "umount /dev/sda1"
echo `date` ":"  "Rebooting into usb mode."
./pi_pssh.sh -t 10 "/sbin/pi_check_mount_usb"
echo `date` ":"  "Waiting for reboot..."
sleep 120
echo `date` ":"  "Setting up usb-filesystem."
./pi_pssh.sh -t 0 "/opt/setup_usb.sh"
echo `date` ":"  "Done! Rebooting into JFFS."
./pi_pssh.sh "reboot"
echo `date` ":" "Waiting for APs to reboot in jffs mode."
sleep 120
echo `date` ":" "Rebooting into usb and we should be good to do. APs should be up in ~2mins."
./pi_pssh.sh "/sbin/pi_check_mount_usb"

