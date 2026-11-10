#include <assert.h>
#include <errno.h>
#include <netinet/icmp6.h>
#include <ndp.h>
#include <stdio.h>
int main(void) {
 for (int cycle=0;cycle<2;cycle++) {
  struct ndp_msg *bad=NULL;
  assert(ndp_msg_new(&bad,NDP_MSG_ALL)==-EINVAL && bad==NULL);
  for (int type=NDP_MSG_RS;type<NDP_MSG_ALL;type++) {
   struct ndp_msg *msg=NULL;
   assert(ndp_msg_new(&msg,type)==0 && msg);
   assert(ndp_msg_type(msg)==type && ndp_msg_payload(msg));
   size_t len=ndp_msg_payload_len(msg),max=ndp_msg_payload_maxlen(msg);
   assert(len>=sizeof(struct icmp6_hdr) && len<=max);
   ndp_msg_ifindex_set(msg,7);assert(ndp_msg_ifindex(msg)==7);
   ndp_msg_payload_len_set(msg,max+1);assert(ndp_msg_payload_len(msg)==max);
   ndp_msg_payload_len_set(msg,len);assert(ndp_msg_payload_len(msg)==len);
   ndp_msg_destroy(msg);
  }
 }
 puts("{\"message_types\":5,\"cycles\":2,\"wildcard_creation_refused\":true,\"payload_length_clamp_and_recovery\":true,\"actual_NDP_packets_sent\":false}");
 return 0;
}
