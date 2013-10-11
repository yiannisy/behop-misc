
//#define SRV_IP "172.24.74.179"		//thetida
//#define SRV_PORT 5588			//for production
//#define SRV_PORT 5589			//for testing

#define BUFLEN 1600
#define MAX_HDR_LEN 200
#define LOG_ENTRY_SIZE 300

//example filter
const struct sock_filter MGMT_BPF[] = 
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
