iw dev mon0 del
iw dev mon1 del
ip link del veth1
ip link del veth3
# we also need to delete veth pairs ?
wifi
ifconfig wlan0 up
ifconfig wlan1 up
iw dev wlan0 interface add mon0 type monitor
iw dev wlan1 interface add mon1 type monitor
ifconfig mon0 up
ifconfig mon1 up
ip link add type veth
ip link add type veth
ifconfig veth0 up
ifconfig veth1 up
ifconfig veth2 up
ifconfig veth3 up
killall mon_to_tap
killall sta_manager
/etc/init.d/openvswitch restart
ovs-ofctl mod-port br0 2 noflood
ovs-ofctl mod-port br0 4 noflood
/opt/utils/sta_manager &
/opt/utils/mon_to_tap -m mon0 -t veth0 &
/opt/utils/mon_to_tap -m mon1 -t veth2 &
echo 0 > /sys/class/leds/ath9k-phy0/brightness
echo 0 > /sys/class/leds/ath9k-phy1/brightness

