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
sleep 90
echo `date` ":"  "Setting up usb-filesystem. When this completes, the system will reboot on usb mode."
./pi_pssh.sh -t 0 "/opt/setup_usb.sh"


