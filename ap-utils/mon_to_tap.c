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
#include <jansson.h>

static int
device_index(int fd, const char *devname)
{
  struct ifreq req;

  strncpy(req.ifr_name, devname, IFNAMSIZ);
  req.ifr_addr.sa_family = AF_INET;

  if (ioctl(fd, SIOCGIFINDEX, &req) < 0)
    err(1, "Interface %s not found", devname);

  if (req.ifr_ifindex < 0)
    err(1, "Interface %s not found", devname);

  printf("index %d\n", req.ifr_ifindex);
  return req.ifr_ifindex;
}

static int
open_monitor_socket(char * devname){
  struct sockaddr_ll sall;
  int fd;
  int ifindex;

  if ((fd = socket(PF_PACKET, SOCK_RAW, htons(ETH_P_ALL))) < 0){
    printf("Could not create packet socket : %s\n", strerror(errno));
    return -1;
  }
  
  ifindex = device_index(fd, devname);
  memset(&sall, 0, sizeof(struct sockaddr_ll));
  sall.sll_ifindex = ifindex;
  sall.sll_family = AF_PACKET;
  sall.sll_protocol = htons(ETH_P_ALL);
  if (bind(fd, (struct sockaddr*)&sall, sizeof(sall)) < 0){
    printf("Could not bind to interface : %s\n",strerror(errno));
    return -1;
  }
  return fd;
}

void usage(){
  printf("usage : mon_to_tap\n");
  printf("mon_to_tap -m mon0 -t tap0: forwards packets from a monitor interface to a tap interface and vice-verca.\n" \
	 "\t-m : the monitor interface to capture \n" \
	 "\t-t : the tap interface to capture\n"
	 );
}


int main(int argc, char **argv){
  char *tap_intf, * mon_intf;
  int mon_fd, tap_fd; // one socket for each interface
  int rc;
  char buf[8092];
  int r_bytes, w_bytes, bytes_left;
  fd_set rfds, wfds;
  int c;

  struct sock_filter MGMT_BPF[] = 
    {{ 0x30, 0, 0, 0x00000003 },
     { 0x64, 0, 0, 0x00000008 },
     { 0x7, 0, 0, 0x00000000 },
     { 0x30, 0, 0, 0x00000002 },
     { 0x4c, 0, 0, 0x00000000 },
     { 0x2, 0, 0, 0x00000000 },
     { 0x7, 0, 0, 0x00000000 },
     { 0x50, 0, 0, 0x00000000 },
     { 0x45, 2, 0, 0x0000000c },
     { 0x54, 0, 0, 0x000000fc },
     { 0x15, 0, 1, 0x00000080 },
     { 0x6, 0, 0, 0x00000000 },
     { 0x6, 0, 0, 0x0000ffff }};
 struct sock_fprog filter;
 filter.len = 13;
 filter.filter = MGMT_BPF;

  if (argc < 5){
    printf("few arguments given...(%d)\n",argc);
    usage();
    exit(0);
  }

  while ((c = getopt(argc, argv, "m:t:")) != -1)
    switch(c)
      {
      case 'm':
	mon_intf = optarg;
	break;
      case 't':
	tap_intf = optarg;
	break;
      case '?':
	usage();
	exit(0);
      default:
	usage();
	exit(0);
      }

  printf("capturing interfaces : %s <-> %s\n",mon_intf, tap_intf);

  mon_fd = open_monitor_socket(mon_intf);
  if (mon_fd <= 0){
    printf("Cannot open monitor socket...(%s)\n", strerror(mon_fd));
    exit(0);
  }
  /* Capture only mgmt frames (non-beacons) */
  if (setsockopt(mon_fd,SOL_SOCKET, SO_ATTACH_FILTER, &filter, sizeof(filter)) < 0){
    printf("setsockopt cannot attach filter : %s\n",strerror(errno));
    exit(0);
  }

  tap_fd = open_monitor_socket(tap_intf);
  if (tap_fd <= 0){
    printf("Cannot open socket to tap interface...\n");
    exit(0);
  }

  /* Thinks look good - let's fork and exit */
  /* Daemonize code from : http://www.netzmafia.de/skripten/unix/linux-daemon-howto.html */
  /* pid_t pid, sid; */
  /* pid = fork(); */
  /* if (pid < 0){ */
  /*   exit(EXIT_FAILURE); */
  /* } */
  /* if (pid > 0){ */
  /*   exit(EXIT_SUCCESS); // exit parent */
  /* } */
  /* umask(0); */
  /* sid = setsid(); */
  /* if (sid < 0){ */
  /*   exit(EXIT_FAILURE); */
  /* } */
  /* if ((chdir("/")) < 0){ */
  /*   exit(EXIT_FAILURE); */
  /* } */
  /* close(STDIN_FILENO); */
  /* close(STDOUT_FILENO); */
  /* close(STDERR_FILENO); */
  

  while (1){
    FD_ZERO(&rfds);
    FD_ZERO(&wfds);
    FD_SET(mon_fd, &rfds);
    FD_SET(tap_fd, &rfds);
    FD_SET(mon_fd, &wfds);
    FD_SET(tap_fd, &wfds);
    rc = select(sizeof(rfds)*8, &rfds, NULL, NULL, NULL);
    if (rc == -1){
      printf("select failed\n");
      exit(0);
    }

    if (rc > 0){
      if (FD_ISSET(mon_fd, &rfds)){ // && FD_ISSET(tap_fd,&wfds)) {
	r_bytes = recv(mon_fd,buf, 8092,0);
	bytes_left = r_bytes > 1500? 1500 : r_bytes;
	//printf("received %d bytes from mon\n",r_bytes);
	while(bytes_left > 0){
	  w_bytes = send(tap_fd, buf, bytes_left,0);
	  if (w_bytes < 0){
	    printf("failed to send data (%s)\n", strerror(errno));
	    exit(0);
	  }
	  bytes_left -= w_bytes;
	}
      }
      if (FD_ISSET(tap_fd, &rfds)){// && FD_ISSET(mon_fd, &wfds)){
	r_bytes = recv(tap_fd,buf, 8092,0);
	//printf("received %d bytes from tap\n",r_bytes);
	bytes_left = r_bytes > 1500? 1500 : r_bytes;
	while(bytes_left > 0){
	  w_bytes = send(mon_fd, buf, bytes_left,0);
	  if (w_bytes < 0){
	    printf("failed to send data (%s)\n", strerror(errno));
	    exit(0);
	  }
	  bytes_left -= w_bytes;
	}
      }
    }
  }

}
  
