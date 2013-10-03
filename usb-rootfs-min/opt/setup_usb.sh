EXTRA_FILES=/opt/extra_files
CONTROLLER='172.24.74.179'
echo "Disabling dnsmasq"
/etc/init.d/dnsmasq stop
/etc/init.d/dnsmasq disable

echo "Preparing opkg for local updates..."
cp ${EXTRA_FILES}/opkg.conf /etc/opkg.conf
opkg update
echo "Installing dependencies..."
opkg install jansson python kmod-veth tcpdump kmod-ath9k openvswitch-switch python-pcap mini-snmpd

echo "Setting-up openvswitch"
/etc/init.d/openvswitch start
ovs-vsctl add-br br0
ovs-vsctl add-port br0 eth0 -- set interface eth0 ofport_request=1
ovs-vsctl add-port br0 veth1 -- set interface veth1 ofport_request=2
ovs-vsctl add-port br0 wlan0 -- set interface wlan0 ofport_request=3
ovs-vsctl set-controller br0 tcp:${CONTROLLER}:6635
ovs-vsctl set-manager tcp:${CONTROLLER}:9935

echo "Enabling SNMP"
uci set mini_snmpd.@mini_snmpd[0].enabled=1
uci commit mini_snmpd
/etc/init.d/mini_snmpd enable

echo "Enabling new network configuration and startup scripts"
cp ${EXTRA_FILES}/network /etc/config/network
cp ${EXTRA_FILES}/rc.local /etc/rc.local
mkdir -p /opt/utils
cp ${EXTRA_FILES}/sta_manager /opt/utils
cp ${EXTRA_FILES}/mon_to_tap /opt/utils
cp ${EXTRA_FILES}/crontab_root /etc/crontabs/root
cp ${EXTRA_FILES}/authorized_keys /etc/dropbear
cp ${EXTRA_FILES}/passwd /etc/
cp ${EXTRA_FILES}/shadow /etc/

echo "Setting up Wireless"
/sbin/wifi detect > /tmp/wireless.tmp
[ -s /tmp/wireless.tmp ] && {
    cat /tmp/wireless.tmp >> /etc/config/wireless
    uci set wireless.radio0.disabled=0
    uci set wireless.radio0.beacon_int=1000
    uci delete wireless.@wifi-iface[0].network
    uci set wireless.@wifi-iface[0].hidden=1
    uci set wireless.@wifi-iface[0].wmm=1
    uci set wireless.@wifi-iface[0].macaddr=02:00:00:00:00:00

    uci commit wireless
}
rm -f /tmp/wireless.tmp
wifi

echo "Configuration completed - reboot AP to apply all changes!"