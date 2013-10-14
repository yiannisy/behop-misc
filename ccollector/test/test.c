#include <stdio.h>
#include <stdlib.h>
#include <jansson.h>
#include <linux/filter.h>

static inline int
install_filter(char * intf, char * filter_text) {
  FILE *fp;
  int status;
  char fil[40];
  char cmd[1035];
  struct sock_filter * FILTER;
  int filter_len;

  //sprintf(cmd, "tcpdump -dd -i %s %s", intf, filter_text);
  sprintf(cmd, "tcpdump -ddd -i %s %s", intf, filter_text);
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
  int i = 0;
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

  return 0;
}

static inline int
do_ls_etc() {
  FILE *fp;
  int status;
  char path[1035];

  /* Open the command for reading. */
  fp = popen("/bin/ls /etc/", "r");
  if (fp == NULL) {
    printf("Failed to run command\n" );
    exit;
  }

  /* Read the output a line at a time - output it. */
  while (fgets(path, sizeof(path)-1, fp) != NULL) {
    printf("%s", path);
  }

  /* close */
  pclose(fp);

  return 0;
}

int main() {
  char intf[] = "mon0";		//any interface name so that tcpdump doesn't complain
  char filter_text[] = "type data or subtype ack";
  //do_ls_etc();
  install_filter(intf, filter_text);
}
