#include <stdio.h>

#include <string.h> /* for strncpy */

#include <sys/types.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <netinet/in.h>
#include <net/if.h>
#include <arpa/inet.h>


static inline int
get_ip_of_intf(char * intf, char * ip) {
 int fd;
 struct ifreq ifr;

 fd = socket(AF_INET, SOCK_DGRAM, 0);

 /* I want to get an IPv4 IP address */
 ifr.ifr_addr.sa_family = AF_INET;

 /* I want IP address attached to "eth0" */
 //strncpy(ifr.ifr_name, "eth0", IFNAMSIZ-1);
 strncpy(ifr.ifr_name, intf, IFNAMSIZ-1);

 ioctl(fd, SIOCGIFADDR, &ifr);

 close(fd);

 strcpy(ip, inet_ntoa(((struct sockaddr_in *)&ifr.ifr_addr)->sin_addr));

 /* display result */
 //printf("%s\n", inet_ntoa(((struct sockaddr_in *)&ifr.ifr_addr)->sin_addr));
 printf("%s\n", ip);

 return 0;
}


static inline int
install_filter(char * intf, char * filter_text, struct sock_fprog *filter) {

  struct sock_filter * FILTER = NULL;
  FILE *fp;
  int status;
  char fil[40];
  char cmd[1035];
  int filter_len;
  int i = 0;

  //sprintf(cmd, "tcpdump -dd -i %s %s", intf, filter_text);
  sprintf(cmd, "tcpdump -ddd -i %s \"%s\"", intf, filter_text);
  printf("cmd: %s\n", cmd);

  /* Open the command for reading. */
  fp = popen(cmd, "r");
  if (fp == NULL) {
    printf("Failed to run command\n" );
    exit;
  }


  /* Read the output a line at a time - output it. */
  fgets(fil, sizeof(fil)-1, fp);
  filter_len = atoi(fil);
  //printf("len: %d\n", filter_len);

  FILTER = (struct sock_filter *)(malloc(sizeof(struct sock_filter) * filter_len));

  //while (fgets(fil, sizeof(fil)-1, fp) != NULL) {
  for (i = 0; i < filter_len; i++) {
    struct sock_filter * filter_line = &FILTER[i];
    int n;
    char del = ' ';

    if (fgets(fil, sizeof(fil)-1, fp) == NULL) {
      printf("Error creating filter\n");
      exit(0);
    }

    //printf("%s", fil);
    n = atoi(strtok(fil, &del));
    //printf("val=%d  ", n);
    filter_line->code = (unsigned short)n;

    n = atoi(strtok(NULL, &del));
    //printf("val=%d  ", n);
    filter_line->jt = (unsigned char)n;

    n = atoi(strtok(NULL, &del));
    //printf("val=%d  ", n);
    filter_line->jf = (unsigned char)n;

    n = atoi(strtok(NULL, &del));
    //printf("val=%d  ", n);
    filter_line->k = (unsigned int)n;

    //printf("\n");
  }

  printf("created filter structure\n");

  /* close */
  pclose(fp);

  filter->len = filter_len;
  filter->filter = FILTER;
  return 0;
}
