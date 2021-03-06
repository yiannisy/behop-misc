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
#define WLAN0_BSSIDMASK_DEBUGFS_FILE "/sys/kernel/debug/ieee80211/phy0/ath9k/bssidmask"
#define WLAN0_ADD_VBEACON_DEBUGFS_FILE "/sys/kernel/debug/ieee80211/phy0/ath9k/addbeacon"
#define WLAN0_DEL_VBEACON_DEBUGFS_FILE "/sys/kernel/debug/ieee80211/phy0/ath9k/delbeacon"
#define WLAN1_BSSIDMASK_DEBUGFS_FILE "/sys/kernel/debug/ieee80211/phy1/ath9k/bssidmask"
#define WLAN1_ADD_VBEACON_DEBUGFS_FILE "/sys/kernel/debug/ieee80211/phy1/ath9k/addbeacon"
#define WLAN1_DEL_VBEACON_DEBUGFS_FILE "/sys/kernel/debug/ieee80211/phy1/ath9k/delbeacon"
#define STA_MANAGER_LOG_FNAME "/var/log/stamanager.log"


#define MON_ID_STA 0
#define MON_ID_CHANNEL 1
#define MON_ID_BSSIDMASK 2
#define MON_ID_POWER 3
#define MON_ID_BEACON 4

#define MONITOR_OVSDB "{\"method\":\"monitor\",\"params\":[\"Open_vSwitch\",0,{\"Wireless\":[{\"columns\":[\"channel\",\"power\",\"ssid\"]}]}],\"id\":1}"

int send_sync(struct nl_sock * sk, struct nl_msg * msg);
void str_to_mac(const char * str, uint8_t * addr);
struct json_t;

static FILE * f_log = NULL;
static char * log_fname = STA_MANAGER_LOG_FNAME;

static const char ifname[] = "wlan1";
//static size_t sta_rates_len = 9;
//static uint8_t sta_rates[9] = {2,11,12,18,24,48,72,96,108};
//static uint16_t sta_aid = 1;
//static uint16_t sta_interval =8;

struct station;
static struct station stations;
static uint8_t base_hw_addr[6] = {0x02,0x00,0x00,0x00,0x00,0x00};


struct station
{
  uint8_t addr[ETH_ALEN];
  uint8_t vbssid[ETH_ALEN];
  struct list_head list;
};

struct ieee80211_ht_capabilities
{
  uint16_t ht_capabilities_info;
  uint8_t a_mpdu_params;
  uint8_t supported_mcs_set[16];
  uint16_t ht_extended_capabilities;
  uint32_t tx_bf_capability_info;
  uint8_t asel_capabilities;
} STRUCT_PACKED;

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
    fprintf(f_log,"message to set AP mode sent with error : %d (%s)\n", err, strerror(err));
  }
  else
    return 0;

nla_put_failure:
  nlmsg_free(msg);
  fprintf(f_log,"failed to change mode to AP\n");
  return ret;
}

void remove_station(struct nl_sock *sock, json_t * update)
{
  struct nl_msg *msg;
  int nl80211_id;
  int err;
  uint8_t addr[6];
  const char * addr_str;
  const char * intf;
  struct list_head *pos, *q;
  struct station *tmp;

  /* Get station from ovsdb update. */
  //fprintf(f_log,"%s\n",json_dumps(update, JSON_ENCODE_ANY));
  addr_str = json_string_value(json_object_get(json_object_get(update,"old"), "addr"));
  intf = json_string_value(json_object_get(json_object_get(update,"old"),"intf"));
  str_to_mac(addr_str, addr);

  fprintf(f_log,"Removing Station :  address : %s \n",addr_str);
  fflush(f_log);

  /* Get the id for nl80211 */
  nl80211_id = genl_ctrl_resolve(sock,"nl80211");
  
  msg = nlmsg_alloc();
  genlmsg_put(msg, NL_AUTO_PID, NL_AUTO_SEQ, nl80211_id, 0, 0, NL80211_CMD_DEL_STATION, 0);
  NLA_PUT_U32(msg, NL80211_ATTR_IFINDEX, if_nametoindex(intf));
  NLA_PUT(msg, NL80211_ATTR_MAC, ETH_ALEN, addr);
  
  //fprintf(f_log,"About to send nl msg to remove station : %s\n", addr_str);
  if ((err = send_sync(sock, msg)) < 0){
    //fprintf(f_log,"message sent with error : %d (%s)\n", err, strerror(err));
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

  fprintf(f_log,"Removed Station :  address : %s \n",addr_str);
  fflush(f_log);
  //fprintf(f_log,"Sent nl msg to remove station : %s\n", addr_str);
  return;
  
 nla_put_failure:
  nlmsg_free(msg);
  //fprintf(f_log,"failure\n");

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

/* Transforms a hex-byte-string to a byte array. Returns 
 * the number of bytes transformed.
 */
size_t str_to_barray(const char * str, uint8_t * buf)
{
  int i;
  char byte[2];
  size_t len;
  len = strlen(str)/2;
  for (i=0; i < len; i++){
    memcpy(byte, &str[2*i], 2);
    buf[i] = (uint8_t) strtoul(byte, NULL, 16);
  }
  return len;
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
  const char * intf;
  char * vbeacon_fname;

  FILE * f = NULL;

  /* Get station and vbssid from ovsdb update. */
  vbssid_str = json_string_value(json_object_get(json_object_get(update,"new"), "vbssid"));
  intf = json_string_value(json_object_get(json_object_get(update,"new"),"intf"));


  if (strcmp(intf,"wlan0") == 0){
    vbeacon_fname = WLAN0_ADD_VBEACON_DEBUGFS_FILE;
  }
  else if(strcmp(intf, "wlan1") == 0){
    vbeacon_fname = WLAN1_ADD_VBEACON_DEBUGFS_FILE;
  }


  if ((f = fopen(vbeacon_fname,"w")) == NULL){
    fprintf(f_log,"cannot open addbeacon file...\n");
    return;
  }
  str_to_mac(vbssid_str, vbssid);

  fprintf(f,"%hhx:%hhx:%hhx:%hhx:%hhx:%hhx\n",vbssid[0], vbssid[1], vbssid[2],
	  vbssid[3],vbssid[4],vbssid[5]);
  fprintf(f_log,"Adding vbeacon for vbssid : %hhx:%hhx:%hhx:%hhx:%hhx:%hhx\n",vbssid[0], vbssid[1], vbssid[2],
	  vbssid[3],vbssid[4],vbssid[5]);

  if (f)
    fclose(f);
}

void del_vbeacon(json_t *update)
{
  uint8_t vbssid[6];
  const char * vbssid_str;
  const char * intf;
  char * vbeacon_fname;
  FILE * f = NULL;

  /* Get station and vbssid from ovsdb update. */
  vbssid_str = json_string_value(json_object_get(json_object_get(update,"old"), "vbssid"));
  intf = json_string_value(json_object_get(json_object_get(update,"old"),"intf"));

  if (!vbssid_str || !intf){
    fprintf(f_log,"cannot parse vbssid or intf---skipping...\n");
    return;
  }

  if (strcmp(intf,"wlan0") == 0){
    vbeacon_fname = WLAN0_DEL_VBEACON_DEBUGFS_FILE;
  }
  else if(strcmp(intf, "wlan1") == 0){
    vbeacon_fname = WLAN1_DEL_VBEACON_DEBUGFS_FILE;
  }

  fprintf(f_log,"deleting vbeacon\n");
  fprintf(f_log,"using %s\n",vbeacon_fname);

  if ((f = fopen(vbeacon_fname,"w")) == NULL){
    fprintf(f_log,"cannot open delbeacon file...\n");
    return;
  }
  str_to_mac(vbssid_str, vbssid);

  fprintf(f,"%hhx:%hhx:%hhx:%hhx:%hhx:%hhx\n",vbssid[0], vbssid[1], vbssid[2],
	  vbssid[3],vbssid[4],vbssid[5]);

  fprintf(f_log,"Deleting vbeacon for vbssid : %hhx:%hhx:%hhx:%hhx:%hhx:%hhx\n",vbssid[0], vbssid[1], vbssid[2],
	  vbssid[3],vbssid[4],vbssid[5]);

  if (f)
    fclose(f);
}


int add_station(struct nl_sock * sock, json_t * update)
{
  struct nl_msg *msg;
  int nl80211_id;
  int err;
  uint8_t addr[6], vbssid[6];
  struct nl80211_sta_flag_update upd;
  const char * vbssid_str, * addr_str;
  const char * intf;
  int sta_exists = 0;
  struct list_head *pos, *q;
  struct station *tmp, *sta;
  uint16_t sta_aid, sta_interval, sta_capability;
  uint8_t sta_rates[16];
  size_t sta_rates_len = 0;

  const char * sta_rates_str, * ext_rates_str,  * mcs_str;

  struct ieee80211_ht_capabilities ht_capa;

  /* Get station and vbssid from ovsdb update. */
  fprintf(f_log,"%s\n",json_dumps(update, JSON_ENCODE_ANY));
  addr_str = json_string_value(json_object_get(json_object_get(update,"new"), "addr"));
  vbssid_str = json_string_value(json_object_get(json_object_get(update,"new"), "vbssid"));
  intf = json_string_value(json_object_get(json_object_get(update,"new"),"intf"));
  sta_aid = json_integer_value(json_object_get(json_object_get(update,"new"),"sta_aid"));
  sta_interval = json_integer_value(json_object_get(json_object_get(update,"new"),"sta_interval"));
  sta_capability = json_integer_value(json_object_get(json_object_get(update,"new"),"sta_capability"));
  sta_rates_str = json_string_value(json_object_get(json_object_get(update,"new"),"sup_rates"));
  ext_rates_str = json_string_value(json_object_get(json_object_get(update,"new"),"ext_rates"));
  ht_capa.ht_capabilities_info = json_integer_value(json_object_get(json_object_get(update,"new"), "ht_capa_info"));
  ht_capa.a_mpdu_params = json_integer_value(json_object_get(json_object_get(update,"new"), "ht_capa_ampdu"));
  mcs_str = json_string_value(json_object_get(json_object_get(update,"new"),"ht_capa_mcs"));
  str_to_barray(mcs_str, ht_capa.supported_mcs_set);
  ht_capa.ht_extended_capabilities = json_integer_value(json_object_get(json_object_get(update,"new"), "ht_capa_ext"));
  ht_capa.tx_bf_capability_info = json_integer_value(json_object_get(json_object_get(update,"new"), "ht_capa_txbf"));
  ht_capa.asel_capabilities = json_integer_value(json_object_get(json_object_get(update,"new"), "ht_capa_asel"));

  fprintf(f_log,"Adding Station :  address : %s | vbssid : %s | sta_aid : %d | sta_interval : %d | sup_rates : %s | ext_rates : %s\n",
	 addr_str, vbssid_str, sta_aid, sta_interval, sta_rates_str, ext_rates_str);
  
  str_to_mac(vbssid_str, vbssid);
  str_to_mac(addr_str, addr);
  sta_rates_len = str_to_barray(sta_rates_str,sta_rates);
  sta_rates_len += str_to_barray(ext_rates_str, sta_rates+sta_rates_len);

  /* Get the id for nl80211 */
  nl80211_id = genl_ctrl_resolve(sock,"nl80211");
  
  /* build the message */
  msg = nlmsg_alloc();
  genlmsg_put(msg, NL_AUTO_PID, NL_AUTO_SEQ, nl80211_id, 0, 0, NL80211_CMD_NEW_STATION, 0);
    
  /* Add attributes */
  NLA_PUT_U32(msg, NL80211_ATTR_IFINDEX, if_nametoindex(intf));
  NLA_PUT(msg, NL80211_ATTR_MAC, ETH_ALEN, addr);
  NLA_PUT(msg, NL80211_ATTR_STA_SUPPORTED_RATES, sta_rates_len, sta_rates);
  NLA_PUT_U16(msg, NL80211_ATTR_STA_AID, sta_aid);
  NLA_PUT_U16(msg, NL80211_ATTR_STA_LISTEN_INTERVAL, sta_interval);
  NLA_PUT_U16(msg, NL80211_ATTR_STA_CAPABILITY, sta_capability);

  /* Check for HT attributes. We assume that if ht_capa_info == 0
   * sta doesn't support them... */
  if (ht_capa.ht_capabilities_info){
    NLA_PUT(msg, NL80211_ATTR_HT_CAPABILITY,
	    sizeof(ht_capa), &ht_capa);
  }

  memset(&upd, 0, sizeof(upd));
  /* add the authorized bit... */
  upd.mask = 1 << NL80211_STA_FLAG_AUTHORIZED;
  upd.mask |= 1 << NL80211_STA_FLAG_SHORT_PREAMBLE;
  upd.mask |= 1 << NL80211_STA_FLAG_WME;
  upd.set = upd.mask;
  
  NLA_PUT(msg, NL80211_ATTR_STA_FLAGS2, sizeof(upd), &upd);
  NLA_PUT(msg, NL80211_ATTR_STA_EXT_CAPABILITY, ETH_ALEN, vbssid);

  struct nlattr *wme = nla_nest_start(msg, NL80211_ATTR_STA_WME);
  if (!wme)
    goto nla_put_failure;
  NLA_PUT_U8(msg, NL80211_STA_WME_UAPSD_QUEUES,
  	     0);
  NLA_PUT_U8(msg, NL80211_STA_WME_MAX_SP,0);
  nla_nest_end(msg, wme);


  err = send_sync(sock, msg);
  if (err < 0 && err != -6){
    fprintf(f_log,"message sent with error : %d (%s)\n", err, strerror(err));
  } 
  else {
    /* add station to our list if it's not already there... */
    list_for_each_safe(pos, q, &(stations.list)){
      tmp = list_entry(pos, struct station, list);
      if (!memcmp(tmp->addr, addr, ETH_ALEN))
	sta_exists = 1;
    }
    if(!sta_exists){
      sta = (struct station *) malloc(sizeof(struct station));
      if (!sta){
	fprintf(f_log,"Cannot allocate memory for new sta...\n");
	return -ENOMEM;
      }
      memcpy(sta->addr, addr, ETH_ALEN);
      memcpy(sta->vbssid, vbssid, ETH_ALEN);
      list_add( &sta->list, &(stations.list));
    }
  }
  return 0;

 nla_put_failure:
  nlmsg_free(msg);
  return -1;
  //fprintf(f_log,"failure\n");

}
  
int ovsdb_connect()
{
  int fd;
  struct sockaddr_un serv_addr;
  char buf[2000];
  int len;

  memset(buf, '0',sizeof(buf));

  if ((fd = socket(AF_UNIX, SOCK_STREAM, 0)) < 0){
    fprintf(f_log,"Cannot allocate socket\n");
    return -1;
  }
    
  memset(&serv_addr, 0, sizeof(serv_addr));
  serv_addr.sun_family = AF_UNIX;
  strcpy(serv_addr.sun_path,OVSDB_UNIX_FILE);
  len = strlen(serv_addr.sun_path) + sizeof(serv_addr.sun_family);
  if (connect(fd, (struct sockaddr *)&serv_addr, len) < 0){
    fprintf(f_log,"Cannot connect to ovsdb-server (%d : %s)\n",-1,strerror(errno));
    close(fd);
    return -1;
  }
  
  return fd;
}

/* Subscribe to updates from DB updates on the ovsdb-server. */
int ovsdb_subscribe(int fd)
{
  int bytes_sent;
  char * json_dump;

  struct json_t * packed_req_channel, *packed_req_power, *packed_req_bssidmask, 
    * packed_req_sta, * packed_req_beacon;

  packed_req_sta = json_pack("{s:s,s:[s,i,{s:[{s:{s:b}}]}],s:i}",
				"method","monitor","params","Wifi_vSwitch",MON_ID_STA,
				"WifiSta","select","initial",0,"id",1);
  packed_req_channel = json_pack("{s:s,s:[s,i,{s:[{s:[s,s],s:{s:b}}]}],s:i}",
			     "method","monitor","params","Wifi_vSwitch",MON_ID_CHANNEL,
				 "WifiConfig","columns","channel","intf","select","initial",0,"id",2);
  packed_req_bssidmask = json_pack("{s:s,s:[s,i,{s:[{s:[s,s],s:{s:b}}]}],s:i}",
			     "method","monitor","params","Wifi_vSwitch",MON_ID_BSSIDMASK,
				   "WifiConfig","columns","bssidmask","intf","select","initial",0,"id",3);
  packed_req_power = json_pack("{s:s,s:[s,i,{s:[{s:[s,s],s:{s:b}}]}],s:i}",
			     "method","monitor","params","Wifi_vSwitch",MON_ID_POWER,
			       "WifiConfig","columns","power","intf","select","initial",0,"id",4);
  packed_req_beacon = json_pack("{s:s,s:[s,i,{s:[{s:{s:b}}]}],s:i}",
				"method","monitor","params","Wifi_vSwitch",MON_ID_BEACON,
				"WifiBeacon","select","initial",0,"id",5);



  json_dump = json_dumps(packed_req_channel, JSON_ENCODE_ANY);
  bytes_sent = write(fd, json_dump, strlen(json_dump));

  json_dump = json_dumps(packed_req_power, JSON_ENCODE_ANY);
  bytes_sent = write(fd, json_dump, strlen(json_dump));

  json_dump = json_dumps(packed_req_bssidmask, JSON_ENCODE_ANY);
  bytes_sent = write(fd, json_dump, strlen(json_dump));


  json_dump = json_dumps(packed_req_sta, JSON_ENCODE_ANY);
  bytes_sent = write(fd, json_dump, strlen(json_dump));
  
  json_dump = json_dumps(packed_req_beacon, JSON_ENCODE_ANY);
  bytes_sent = write(fd, json_dump, strlen(json_dump));

  return 0;
}

void process_sta_update(struct nl_sock *nl_sock, struct json_t * json_obj){
  struct json_t * table_updates;
  void *iter;
  const char *key;
  json_t * val;

  /* find whether this is addition or removal */
  /* pick-up the tables-update part */
  table_updates = json_object_get(json_array_get(json_object_get(json_obj,"params"), 1), "WifiSta");  
  json_object_foreach(table_updates, key, val){
    if ((iter = json_object_iter_at(val,"new")) != NULL){
      add_station(nl_sock, val);
      //add_vbeacon(val);
    }
    else if((iter = json_object_iter_at(val, "old")) != NULL){
      remove_station(nl_sock, val);
      //del_vbeacon(val);
    }
    else{
      fprintf(f_log,"nothing got detected...\n");
    }
  }
}

void process_vbeacon_update(struct json_t * json_obj){
  struct json_t * table_updates;
  void *iter;
  const char *key;
  json_t *val;

  /* find whether this is addition or removal */
  /* pick-up the tables-update part */
  table_updates = json_object_get(json_array_get(json_object_get(json_obj,"params"), 1), "WifiBeacon");  
  json_object_foreach(table_updates, key, val){
    if ((iter = json_object_iter_at(val,"new")) != NULL){
      add_vbeacon(val);
    }
    else if((iter = json_object_iter_at(val, "old")) != NULL){
      del_vbeacon(val);
    }
    else{
      fprintf(f_log,"nothing got detected...\n");
    }
  }
}


void process_bssidmask_update(struct json_t * update){
  FILE * f = NULL;
  const char * bssidmask_str;
  const char * intf;
  const char * bssid_fname;
  uint8_t bssidmask[6];
  struct json_t * table_update;
  const char *key;
  json_t * val;
  void * iter;

  table_update = json_object_get(json_array_get(json_object_get(update,"params"), 1), "WifiConfig");  
  json_object_foreach(table_update, key, val){
    if ((iter = json_object_iter_at(val, "new")) != NULL){
      bssidmask_str = json_string_value(json_object_get(json_object_get(val,"new"), "bssidmask"));
      intf = json_string_value(json_object_get(json_object_get(val,"new"),"intf"));
      if (!bssidmask_str || !intf){
	fprintf(f_log,"cannot decode bssidmask/intf - skipping\n");
	return;
      }
      break;
    }
  }
  str_to_mac(bssidmask_str, bssidmask);
  if (strcmp(intf,"wlan0") == 0){
    bssid_fname = WLAN0_BSSIDMASK_DEBUGFS_FILE;
  }
  else if(strcmp(intf, "wlan1") == 0){
    bssid_fname = WLAN1_BSSIDMASK_DEBUGFS_FILE;
  }

  /* now write the value to debugfs */
  if ((f = fopen(bssid_fname, "w")) == NULL){
    fprintf(f_log,"cannot open bssidmask file...\n");
    return;
  }
  
  fprintf(f_log,"Updating BSSIDMASK : %hhx:%hhx:%hhx:%hhx:%hhx:%hhx\n",bssidmask[0], bssidmask[1], bssidmask[2],
	 bssidmask[3],bssidmask[4],bssidmask[5]);
  
  fprintf(f,"%hhx:%hhx:%hhx:%hhx:%hhx:%hhx\n",bssidmask[0], bssidmask[1], bssidmask[2],
	  bssidmask[3],bssidmask[4],bssidmask[5]);
  if (f)
    fclose(f);
}

void process_channel_update(struct json_t * update){
  fprintf(f_log,"channel update not supported yet\n");
  return;
}

void process_power_update(struct json_t * update){
  fprintf(f_log,"power update not supported yet\n");
  return;
}

void ovsdb_monitor(int fd, struct nl_sock *nl_sock)
{
  int n, decoded;
  char buf[8000];
  json_error_t json_err;
  struct json_t * json_ret;
  const char * method;

  while((n = read(fd, buf, sizeof(buf))) > 0){
    decoded = 0;
    while((decoded < n) && (decoded >= 0)){
      json_ret = json_loads(buf + decoded,JSON_DISABLE_EOF_CHECK,&json_err);
      if (!json_ret){
	fprintf(f_log,"Cannot decode json message - skipping (%s)\n",buf);
	memset(buf,0,sizeof(buf));
	break;
      }
      else{
	decoded += json_err.position;
      }
      method = json_string_value(json_object_get(json_ret, "method"));
      if (method == NULL){ 
	memset(buf,0,sizeof(buf));
	break;
      }
      if (!strcmp(method,"update")){
	/* Look at the MON_ID to see what is being updated. */
	int mon_id = json_integer_value(json_array_get(json_object_get(json_ret,"params"),0));
	fprintf(f_log,"Processing an update for MON_ID : %d\n",mon_id);
	switch(mon_id) {
	case MON_ID_STA:
	  process_sta_update(nl_sock, json_ret);
	  break;
	case MON_ID_CHANNEL:
	  process_channel_update(json_ret);
	  break;
	case MON_ID_BSSIDMASK:
	  process_bssidmask_update(json_ret);
	  break;
	case MON_ID_POWER:
	  process_power_update(json_ret);
	  break;
	case MON_ID_BEACON:
	  process_vbeacon_update(json_ret);
	  break;
	default:
	  break;
	}
      }
    }
    memset(buf,0,sizeof(buf));
    fflush(f_log);
  }
}

int main()
{
  struct nl_sock * nl_sock;
  int ovsdb_fd;

  if ((f_log = fopen(log_fname,"w")) == NULL){
    printf("Cannot open log file---closing...\n");
    return -1;
  }
  else{
    printf("Logging!\n");
    fprintf(f_log,"sta_manager starting...\n");
    fflush(f_log);
  }
  /* Initialize a list for stations */
  
  INIT_LIST_HEAD(&(stations.list));

  /* open a netlink socket */
  nl_sock = nl_socket_alloc();

  if(genl_connect(nl_sock)){
    fprintf(f_log,"nl80211: Failed to connect to generic netlink\n");
  }

  if ((ovsdb_fd = ovsdb_connect()) < 0){
    fprintf(f_log,"cannot connect to ovsdb-server - quit...\n");
    return 0;
  }

  fprintf(f_log,"Connected to ovsdb-server\n");
  ovsdb_subscribe(ovsdb_fd);
    
  ovsdb_monitor(ovsdb_fd, nl_sock);
  
  fclose(f_log);
  return 0;
}
