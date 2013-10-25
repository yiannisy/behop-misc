#include <unistd.h>
#include <stdio.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <net/ethernet.h>
#include <netpacket/packet.h>
#include <string.h>
#include <linux/if_ether.h>
#include <linux/filter.h>
#include <stdlib.h>
#include <errno.h>
#include <arpa/inet.h>
#include <netinet/in.h>

#include "../util.h"


int main() {
  char * SRV_IP, * SRV_PORT;
  uint32_t iSRV_PORT;
  //char dst_ip_port[] = "172.31.1.1:5589";
  char dst_ip_port[] = "172.31.1.1:55a89";
  //get_dst_ip_port(dst_ip_port, &SRV_IP, &SRV_PORT);
  get_dst_ip_port(dst_ip_port, &SRV_IP, &iSRV_PORT);
  
  return 0;
}
