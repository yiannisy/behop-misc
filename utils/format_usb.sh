parted /dev/sdb print
parted /dev/sdb rm 1
parted /dev/sdb mkpart primary 1048kB 6200MB
parted /dev/sdb mkpartfs primary linux-swap 6200MB 6712MB
parted /dev/sdb print
mkfs.ext4 /dev/sdb1
mount -t ext4 /dev/sdb1 /media
cp -r /home/yiannis/of/pi-dev/usb-rootfs-min/* /media/
umount /media
echo "done - usb ready!"