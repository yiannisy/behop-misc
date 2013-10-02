#include <stdio.h>
#include <unistd.h>
#include <net/if.h>
#include <linux/types.h>
#include <linux/netlink.h>
#include <netlink/socket.h>
#include <netlink/netlink.h>
#include <netlink/msg.h>
#include <netlink/genl/genl.h>
#include <netlink/genl/family.h>
#include <netlink/genl/ctrl.h>
#include "nl80211_copy.h"
#include <linux/if_ether.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <errno.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <jansson.h>
#include "list.h"

#define OVSDB_PORT 6632
#define LOCALHOST "127.0.0.1"
#define OVSDB_UNIX_FILE "/var/run/db.sock"
#define BSSIDMASK_DEBUGFS_FILE "/sys/kernel/debug/ieee80211/phy0/ath9k/bssidmask"
#define ADD_VBEACON_DEBUGFS_FILE "/sys/kernel/debug/ieee80211/phy0/ath9k/addbeacon"
#define DEL_VBEACON_DEBUGFS_FILE "/sys/kernel/debug/ieee80211/phy0/ath9k/delbeacon"


#define MONITOR_OVSDB "{\"method\":\"monitor\",\"params\":[\"Open_vSwitch\",0,{\"Wireless\":[{\"columns\":[\"channel\",\"power\",\"ssid\"]}]}],\"id\":1}"

static const char ifname[] = "wlan0";
static size_t sta_rates_len = 9;
static uint8_t sta_rates[9] = {2,11,12,18,24,48,72,96,108};
static uint16_t sta_aid = 1;
static uint16_t sta_interval =8;

struct station;
static struct station stations;
static uint8_t base_hw_addr[6] = {0x02,0x00,0x00,0x00,0x00,0x00};


struct station
{
  uint8_t addr[ETH_ALEN];
  uint8_t vbssid[ETH_ALEN];
  struct list_head list;
};

static int wifi_set_ap_mode(struct nl_sock * sock)
{
  int nl80211_id;
  struct nl_msg *msg;
  int err,ret;

  /* Get the id for nl80211 */
  nl80211_id = genl_ctrl_resolve(sock,"nl80211");

  msg = nlmsg_alloc();
  if (!msg)
    return -ENOMEM;
  
  genlmsg_put(msg, NL_AUTO_PID, NL_AUTO_SEQ, nl80211_id, 0, 0, NL80211_CMD_SET_INTERFACE, 0);
  NLA_PUT_U32(msg, NL80211_ATTR_IFINDEX, if_nametoindex(ifname));
  NLA_PUT_U32(msg, NL80211_ATTR_IFTYPE, NL80211_IFTYPE_AP);

  if ((err = send_sync(sock, msg)) < 0){
    printf("message to set AP mode sent with error : %d (%s)\n", err, strerror(err));
  }
  else
    return 0;

nla_put_failure:
  nlmsg_free(msg);
  printf("failed to change mode to AP\n");
  return ret;
}

void update_bssidmask()
{
  struct station *tmp = NULL;
  uint8_t bssidmask[ETH_ALEN];
  int i;
  FILE * f = NULL;

  memset(bssidmask, 0xff, ETH_ALEN);

  list_for_each_entry(tmp, &stations.list, list){
    if (tmp == NULL)
      continue;
    for (i = 0; i < ETH_ALEN; i++){
      bssidmask[i] &= ~(tmp->vbssid[i] ^ base_hw_addr[i]);
    }
  }

  printf("This is the updated mask : %hhx:%hhx:%hhx:%hhx:%hhx:%hhx\n",bssidmask[0], bssidmask[1], bssidmask[2],
	 bssidmask[3],bssidmask[4],bssidmask[5]);


  /* now write the value to debugfs */
  if ((f = fopen(BSSIDMASK_DEBUGFS_FILE, "w")) == NULL){
    printf("cannot open bssidmask file...\n");
    return;
  }
  fprintf(f,"%hhx:%hhx:%hhx:%hhx:%hhx:%hhx\n",bssidmask[0], bssidmask[1], bssidmask[2],
	  bssidmask[3],bssidmask[4],bssidmask[5]);
  if (f)
    fclose(f);
}

void remove_station(struct nl_sock *sock, json_t * update)
{
  struct nl_msg *msg;
  int nl80211_id;
  int err;
  uint8_t addr[6];
  const char * addr_str;
  struct list_head *pos, *q;
  struct station *tmp;

  /* Get station from ovsdb update. */
  printf("%s\n",json_dumps(update, JSON_ENCODE_ANY));
  addr_str = json_string_value(json_object_get(json_object_get(update,"old"), "addr"));
  str_to_mac(addr_str, addr);


  /* Get the id for nl80211 */
  nl80211_id = genl_ctrl_resolve(sock,"nl80211");
  
  msg = nlmsg_alloc();
  genlmsg_put(msg, NL_AUTO_PID, NL_AUTO_SEQ, nl80211_id, 0, 0, NL80211_CMD_DEL_STATION, 0);
  NLA_PUT_U32(msg, NL80211_ATTR_IFINDEX, if_nametoindex(ifname));
  NLA_PUT(msg, NL80211_ATTR_MAC, ETH_ALEN, addr);
  
  printf("About to send nl msg to remove station : %s\n", addr_str);
  if ((err = send_sync(sock, msg)) < 0){
    printf("message sent with error : %d (%s)\n", err, strerror(err));
  }
  else {
    /* delete the station if it's on the list */
    list_for_each_safe(pos, q, &(stations.list)){
      tmp = list_entry(pos, struct station, list);
      if (!memcmp(tmp->addr, addr, ETH_ALEN)){
	list_del(pos);
	free(tmp);
      }
    }
  }
  printf("Sent nl msg to remove station : %s\n", addr_str);
  return;
  
 nla_put_failure:
  nlmsg_free(msg);
  printf("failure\n");

}

void str_to_mac(const char * str, uint8_t * addr)
{
  int i;
  char byte[2];
  for (i=0; i < 6; i++){
    memcpy(byte, &str[2*i], 2);
    addr[i] = (uint8_t) strtoul(byte, NULL, 16);
  }
}

int send_sync(struct nl_sock * sk, struct nl_msg * msg)
{
  int err;
  err = nl_send_auto_complete(sk, msg);
  nlmsg_free(msg);
  if (err < 0){
    return err;
  }
  return nl_wait_for_ack(sk);
}

void add_vbeacon(json_t *update)
{
  uint8_t vbssid[6];
  const char * vbssid_str;
  FILE * f = NULL;

  /* Get station and vbssid from ovsdb update. */
  vbssid_str = json_string_value(json_object_get(json_object_get(update,"new"), "vbssid"));
  printf("Opening vbeacon file\n");
  if ((f = fopen(ADD_VBEACON_DEBUGFS_FILE,"w")) == NULL){
    printf("cannot open addbeacon file...\n");
    return;
  }
  str_to_mac(vbssid_str, vbssid);

  fprintf(f,"%hhx:%hhx:%hhx:%hhx:%hhx:%hhx\n",vbssid[0], vbssid[1], vbssid[2],
	  vbssid[3],vbssid[4],vbssid[5]);
  printf("Closing vbeacon file\n");
  if (f)
    fclose(f);
  printf("closed\n");
}

void del_vbeacon(json_t *update)
{
  uint8_t vbssid[6];
  const char * vbssid_str;
  FILE * f = NULL;

  /* Get station and vbssid from ovsdb update. */
  vbssid_str = json_string_value(json_object_get(json_object_get(update,"old"), "vbssid"));
  printf("Opening vbeacon file\n");
  if ((f = fopen(DEL_VBEACON_DEBUGFS_FILE,"w")) == NULL){
    printf("cannot open delbeacon file...\n");
    return;
  }
  str_to_mac(vbssid_str, vbssid);

  fprintf(f,"%hhx:%hhx:%hhx:%hhx:%hhx:%hhx\n",vbssid[0], vbssid[1], vbssid[2],
	  vbssid[3],vbssid[4],vbssid[5]);
  printf("Closing vbeacon file\n");
  if (f)
    fclose(f);
  printf("Closed\n");
}


void add_station(struct nl_sock * sock, json_t * update)
{
  struct nl_msg *msg;
  int nl80211_id;
  int err;
  uint8_t addr[6], vbssid[6];
  struct nl80211_sta_flag_update upd;
  const char * vbssid_str, * addr_str;
  int sta_exists = 0;
  struct list_head *pos, *q;
  struct station *tmp, *sta;


  /* Get station and vbssid from ovsdb update. */
  printf("%s\n",json_dumps(update, JSON_ENCODE_ANY));
  addr_str = json_string_value(json_object_get(json_object_get(update,"new"), "addr"));
  vbssid_str = json_string_value(json_object_get(json_object_get(update,"new"), "vbssid"));
  printf("This is the station address : %s | vbssid : %s\n",addr_str, vbssid_str);

  str_to_mac(vbssid_str, vbssid);
  str_to_mac(addr_str, addr);

  /* Get the id for nl80211 */
  nl80211_id = genl_ctrl_resolve(sock,"nl80211");
  
  /* build the message */
  msg = nlmsg_alloc();
  genlmsg_put(msg, NL_AUTO_PID, NL_AUTO_SEQ, nl80211_id, 0, 0, NL80211_CMD_NEW_STATION, 0);
    
  /* Add attributes */
  NLA_PUT_U32(msg, NL80211_ATTR_IFINDEX, if_nametoindex(ifname));
  NLA_PUT(msg, NL80211_ATTR_MAC, ETH_ALEN, addr);
  NLA_PUT(msg, NL80211_ATTR_STA_SUPPORTED_RATES, sta_rates_len, sta_rates);
  NLA_PUT_U16(msg, NL80211_ATTR_STA_AID, sta_aid);
  NLA_PUT_U16(msg, NL80211_ATTR_STA_LISTEN_INTERVAL, sta_interval);

  memset(&upd, 0, sizeof(upd));
  /* add the authorized bit... */
  upd.mask = 1 << NL80211_STA_FLAG_AUTHORIZED;
  upd.mask |= 1 << NL80211_STA_FLAG_SHORT_PREAMBLE;
  upd.set = upd.mask;
  
  NLA_PUT(msg, NL80211_ATTR_STA_FLAGS2, sizeof(upd), &upd);
  NLA_PUT(msg, NL80211_ATTR_STA_EXT_CAPABILITY, ETH_ALEN, vbssid);


  printf("About to send message to add station %s\n",addr_str);
  err = send_sync(sock, msg);
  if (err < 0 && err != -6){
    printf("message sent with error : %d (%s)\n", err, strerror(err));
  } 
  else {
    printf("Station added to kernel - checking for BSSIDMASK\n");
    /* add station to our list if it's not already there... */
    list_for_each_safe(pos, q, &(stations.list)){
      tmp = list_entry(pos, struct station, list);
      if (!memcmp(tmp->addr, addr, ETH_ALEN))
	sta_exists = 1;
    }
    if(!sta_exists){
      sta = (struct station *) malloc(sizeof(struct station));
      if (!sta){
	printf("Cannot allocate memory for new sta...\n");
	return -ENOMEM;
      }
      memcpy(sta->addr, addr, ETH_ALEN);
      memcpy(sta->vbssid, vbssid, ETH_ALEN);
      list_add( &sta->list, &(stations.list));
    }
  }
  printf("Sent message to add station %s\n",addr_str);
  return;

 nla_put_failure:
  nlmsg_free(msg);
  printf("failure\n");

}
  
int ovsdb_connect()
{
  int fd;
  struct sockaddr_un serv_addr;
  char buf[2000];
  int len;

  memset(buf, '0',sizeof(buf));

  if ((fd = socket(AF_UNIX, SOCK_STREAM, 0)) < 0){
    printf("Cannot allocate socket\n");
    return -1;
  }
    
  memset(&serv_addr, 0, sizeof(serv_addr));
  serv_addr.sun_family = AF_UNIX;
  strcpy(serv_addr.sun_path,OVSDB_UNIX_FILE);
  len = strlen(serv_addr.sun_path) + sizeof(serv_addr.sun_family);
  if (connect(fd, (struct sockaddr *)&serv_addr, len) < 0){
    printf("Cannot connect to ovsdb-server (%d : %s)\n",-1,strerror(errno));
    close(fd);
    return -1;
  }
  
  return fd;
}

/* Subscribe to updates from DB updates on the ovsdb-server. */
int ovsdb_subscribe(int fd)
{
  int bytes_sent;
  char buf[1000];
  struct json_t * json_obj;
  struct json_t * params_array;
  struct json_t * monitor_request, * monitor_select, * request;
  struct json_t * monitor_request_array;
  char * json_dump;

  struct json_t * packed_req;

  packed_req = json_pack("{s:s,s:[s,i,{s:[{s:[s,s],s:{s:b}}]}],s:i}",
			 "method","monitor","params","Open_vSwitch",0,
			 "WifiSta","columns","addr","vbssid","select","initial",0,"id",1);
  json_dump = json_dumps(packed_req, JSON_ENCODE_ANY);
  printf("JSON_PACKED:%s\n",json_dump);
  bytes_sent = write(fd, json_dump, strlen(json_dump));
  
  printf("sent %d bytes\n", bytes_sent);

  /* no need to manually build json message... */

  /* monitor_select = json_object(); */
  /* json_object_set(monitor_select,"initial",json_false()); */
  
  /* monitor_request = json_object(); */
  /* json_object_set(monitor_request,"select",monitor_select); */

  /* monitor_request_array = json_array(); */
  /* json_array_append(monitor_request_array, monitor_request); */

  /* request = json_object(); */
  /* json_object_set(request,"WifiSta",monitor_request_array); */
  

  /* params_array = json_array(); */
  /* json_array_append(params_array,json_string("Open_vSwitch")); */
  /* json_array_append(params_array, json_integer(0)); */
  /* json_array_append(params_array, request); */
  
  /* json_obj = json_object(); */
  /* json_object_set(json_obj,"method",json_string("monitor")); */
  /* json_object_set(json_obj,"params",params_array); */

  /* json_object_set(json_obj,"id",json_integer(1)); */

  /* json_dump = json_dumps(json_obj, JSON_ENCODE_ANY); */
  /* printf("JSON-DUMP:%s\n",json_dump); */

  /* json_dump = json_dumps(packed_req, JSON_ENCODE_ANY); */
  /* printf("JSON_PACKED:%s\n",json_dump); */
  /* bytes_sent = write(fd, json_dump, strlen(json_dump)); */

  return 0;
}

void ovsdb_monitor(int fd, struct nl_sock *nl_sock)
{
  int n;
  char buf[8000];
  json_error_t json_err;
  struct json_t * json_ret;
  struct json_t * table_updates;
  void *iter;
  const char * method, *id;
  const char *key;
  json_t * val;

  printf("waiting to receive\n");
  while((n = read(fd, buf, sizeof(buf))) > 0){
    printf("Received %d bytes from ovsdb server\n", n);
    printf("%s\n",buf);
    json_ret = json_loads(buf,0,&json_err);
    if (!json_ret){
      printf("Cannot decode json message - skipping\n");
      memset(buf,0,sizeof(buf));
      continue;
    }      
    method = json_string_value(json_object_get(json_ret, "method"));
    if (method == NULL){ 
      memset(buf,0,sizeof(buf));
      continue;
    }
    if (!strcmp(method,"update")){
      /* find whether this is addition or removal */
      /* pick-up the tables-update part */
      table_updates = json_object_get(json_array_get(json_object_get(json_ret,"params"), 1), "WifiSta");
      
      json_object_foreach(table_updates, key, val){
      	if ((iter = json_object_iter_at(val,"new")) != NULL){
      	  printf("New Station Detected!!\n");
	  add_station(nl_sock, val);
	  printf("Updating BSSID mask!!\n");
	  update_bssidmask();
	  printf("Adding vbeacon\n");
	  add_vbeacon(val);
      	}
      	else if((iter = json_object_iter_at(val, "old")) != NULL){
      	  printf("Station to be deleted!!\n");
	  remove_station(nl_sock, val);
	  printf("Updating BSSID mask!!\n");
	  update_bssidmask();
	  printf("Removing vbeacon\n");
	  del_vbeacon(val);
      	}
      	else{
      	  printf("nothing got detected...\n");
      	}
      }
    }
    memset(buf,0,sizeof(buf));
    printf("waiting to receive\n");
  }
}

int main()
{
  struct nl_sock * nl_sock;
  int ovsdb_fd;


  /* Initialize a list for stations */
  
  INIT_LIST_HEAD(&(stations.list));

  /* open a netlink socket */
  nl_sock = nl_socket_alloc();

  if(genl_connect(nl_sock)){
    printf("nl80211: Failed to connect to generic netlink\n");
  }

  /* if(wifi_set_ap_mode(nl_sock)){ */
  /*   printf("nl80211: Failed to set wifi to AP mode\n"); */
  /*   return 0; */
  /* } */

  if ((ovsdb_fd = ovsdb_connect()) < 0){
    printf("cannot connect to ovsdb-server - quit...\n");
    return 0;
  }

  printf("Connected to ovsdb-server\n");
  ovsdb_subscribe(ovsdb_fd);
    
  ovsdb_monitor(ovsdb_fd, nl_sock);
  
  return 0;
}
