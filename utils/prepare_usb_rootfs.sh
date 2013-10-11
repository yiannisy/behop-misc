#!/bin/bash
EXTRA_FILES="../usb-rootfs-min/opt/extra_files"
if [ $# -lt 1 ]
then
    echo "Usage : $0 setup_type (dev, beta, or production)"
    exit
fi

case "$1" in
dev) 
	echo "Setting up usb-rootfs-min for development environment"
	cp ${EXTRA_FILES}/behop.dev ${EXTRA_FILES}/behop
	;;
beta) 
	echo "Setting up usb-rootfs-min for beta environment"
	cp ${EXTRA_FILES}/behop.beta ${EXTRA_FILES}/behop
	;;
production)
	echo "Setting up usb-rootfs-min for production environment"
	cp ${EXTRA_FILES}/behop.production ${EXTRA_FILES}/behop
	;;
*) echo "Invalid option : $@"
	exit
	;;
esac

cp ../ap-utils/sta_manager ${EXTRA_FILES}/
cp ../ap-utils/mon_to_tap  ${EXTRA_FILES}/
cp ../ccollector/ccol_cmd ${EXTRA_FILES}/
cp ../ccollector/ccol ${EXTRA_FILES}/