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
#include <jansson.h>

#include "conf.h"
#include "util.h"

#define UDP

static char apid[20];

void usage(){
  printf("usage : mon_to_tap\n");
  printf("mon_to_tap -m mon0 -t tap0: forwards packets from a monitor interface to a tap interface and vice-verca.\n" \
	 "\t-m : the monitor interface to capture \n" \
	 "\t-t : the tap interface to capture\n"
	 );
}


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

static int
open_udp_socket(char * devname){
  int fd;

  if ((fd = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) < 0){
    printf("Could not create packet socket : %s\n", strerror(errno));
    return -1;
  }
  return fd;
  
}

static int
create_udp_addr(struct sockaddr_in *sin) {
  memset(sin, 0, sizeof(struct sockaddr_in));

  sin->sin_family = AF_INET;
  sin->sin_port = htons(SRV_PORT);
  if (inet_aton(SRV_IP, &sin->sin_addr)==0) {
    fprintf(stderr, "inet_aton() failed\n");
    //exit(1);
    return -1;
  }

  return 0;
}

static int 
serialize_log(char * pkt_buf, int r_bytes, char * ser_buf, int ser_buf_len) {
  //struct json_t * json_packed;
  json_t * json_packed;
  char * json_dump;
  struct timeval tv;
  int len_len = sizeof(int);
  int jso_len;
  int hdr_len;
  int ser_len;

  hdr_len = r_bytes < MAX_HDR_LEN ? r_bytes : MAX_HDR_LEN;
  printf("hdr_len: %d\n", hdr_len);
  pkt_buf[hdr_len] = '\0';	//null terminate before serialization

  printf("ser_buf_len: %d\n", ser_buf_len);

  gettimeofday(&tv,NULL);
  //tv.tv_sec // seconds
  //tv.tv_usec // microseconds

//  json_packed = json_pack("{s:s,s:[s,i,{s:[{s:{s:b}}]}],s:i}",
//				"method","monitor","params","Wifi_vSwitch",MON_ID_STA,
//				"WifiSta","select","initial",0,"id",1);

  printf("tss: %ld, tsu: %ld\n", tv.tv_sec, tv.tv_usec);
  printf("r_bytes: %d\n", r_bytes);

  printf("packing\n");
  json_packed = json_pack("{s:i,s:i,s:i,s:s}", 
  	"tss", tv.tv_sec, 
	"tsu", tv.tv_usec, 
	"len", ser_buf_len,
	//"id", "deadbeef"
	"id", apid
	);

//  json_packed = json_pack("{s:i}", 
//	"len", r_bytes
//	);
  if (json_packed == NULL) {
    printf("Error in json packing\n");
    return -1;
  }

  printf("dumping\n");
  json_dump = json_dumps(json_packed, JSON_ENCODE_ANY);
  if (json_dump == NULL) {
    printf("Error in json dumping\n");
    return -1;
  }
  printf("dumped\n");

  jso_len = strlen(json_dump);

  ser_len = len_len + jso_len + hdr_len;

  if (ser_len > ser_buf_len) {
    printf("Not enough space in ser buf to serialize\n");
    return -1;
  }

  printf("jso_len=%d\n", jso_len);
  int _jso_len = htonl(jso_len);
  memcpy(ser_buf, &_jso_len, sizeof(_jso_len));
 // this is the most confusing c statement I've seen over the last 1-2 years:)
 //((unsigned int *)ser_buf)[0] =  htonl(jso_len);
  memcpy(&ser_buf[4], json_dump, jso_len);
  memcpy(&ser_buf[4 + jso_len], pkt_buf, hdr_len);

  return ser_len;
}

static int 
udp_loop(int mon_fd, int ctl_fd) {
  char buf[BUFLEN];
  int r_bytes, w_bytes, bytes_left;
  fd_set rfds, wfds;
  struct sockaddr_in ctl_sin;
  int rc;

  char ser_buf[LOG_ENTRY_SIZE];
  int ser_len;


  if (create_udp_addr(&ctl_sin) < 0) {
    printf("Could not create ctrl interface sin struct\n");
    exit(0);
  }

  while (1){
    FD_ZERO(&rfds);
    FD_ZERO(&wfds);
    FD_SET(mon_fd, &rfds);
    //FD_SET(mon_fd, &wfds);
    //FD_SET(ctl_fd, &rfds);
    FD_SET(ctl_fd, &wfds);
    rc = select(sizeof(rfds)*8, &rfds, NULL, NULL, NULL);
    if (rc == -1){
      printf("select failed\n");
      exit(0);
    }

    if (rc > 0){
      if (FD_ISSET(mon_fd, &rfds)){ // && FD_ISSET(tap_fd,&wfds)) {
	r_bytes = recv(mon_fd,buf, BUFLEN,0);
	bytes_left = r_bytes > 1500? 1500 : r_bytes;
	printf("received %d bytes from mon\n",r_bytes);

	if ((ser_len = serialize_log(buf, r_bytes, ser_buf, LOG_ENTRY_SIZE)) < 0) {
	  printf("Error serializing log entry\n");
	  exit(0);
	}

	printf("sending\n");
	printf("sending length: %d\n", ser_len);
	//while(bytes_left > 0){
	  //w_bytes = send(tap_fd, buf, bytes_left,0);
	  //bytes_sent = write(fd, json_dump, strlen(json_dump));
	  //w_bytes = sendto(ctl_fd, buf, bytes_left, 0, &ctl_sin, sizeof(ctl_sin));
	w_bytes = sendto(ctl_fd, ser_buf, ser_len, 0, &ctl_sin, sizeof(ctl_sin));

	if (w_bytes < 0){
	  printf("failed to send data over udp ctl interface (%s)\n", strerror(errno));
	  exit(0);
	}
	else {
	  printf("Sent %d bytes\n", w_bytes);
	}
	  //bytes_left -= w_bytes;
	//}
      }
    }
  }
  return 0;
}


#ifndef UDP
static int 
tap_loop(int mon_fd, int tap_fd) {

  char buf[8092];
  int r_bytes, w_bytes, bytes_left;
  fd_set rfds, wfds;
  int rc;

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
#endif 

int main(int argc, char **argv){
  char *tap_intf, * mon_intf, *filter_text;
  int mon_fd, tap_fd; // one socket for each interface
  int ctl_fd;
  int c;

  struct sock_fprog filter;

  if (argc < 5){
    printf("few arguments given...(%d)\n",argc);
    usage();
    exit(0);
  }

  while ((c = getopt(argc, argv, "m:t:f:")) != -1)
    switch(c)
      {
      case 'm':
	mon_intf = optarg;
	break;
      case 't':
	tap_intf = optarg;
	break;
      case 'f':
	filter_text = optarg;
	break;
      case '?':
	usage();
	exit(0);
      default:
	usage();
	exit(0);
      }

  printf("capturing interfaces : %s -> %s\n",mon_intf, tap_intf);

  get_ip_of_intf(tap_intf, apid);

  mon_fd = open_monitor_socket(mon_intf);
  if (mon_fd <= 0){
    printf("Cannot open monitor socket...(%s)\n", strerror(mon_fd));
    exit(0);
  }

#ifndef UDP
  tap_fd = open_monitor_socket(tap_intf);
  if (tap_fd <= 0){
    printf("Cannot open socket to tap interface...\n");
    exit(0);
  }

  /* Capture only mgmt frames (non-beacons) */
  filter.len = 13;
  filter.filter = MGMT_BPF;
#else
  ctl_fd = open_udp_socket(tap_intf);
  if (ctl_fd <= 0) {
    printf("Could not create udp socket\n");
    exit(0);
  }

  if(install_filter(mon_intf, filter_text, &filter) < 0) {
    printf("Could not install filter\n");
    exit(0);
  }
#endif

  /* Apply filter */
  if (setsockopt(mon_fd,SOL_SOCKET, SO_ATTACH_FILTER, &filter, sizeof(filter)) < 0){
    printf("setsockopt cannot attach filter : %s\n",strerror(errno));
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
  
#ifndef UDP
  tap_loop(mon_fd, tap_fd);
#else
  udp_loop(mon_fd, ctl_fd);
#endif

  return 0;
}
  
