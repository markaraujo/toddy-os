#include <unistr.h>
#include <uninorm.h>
#include <unicase.h>
#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(void) {
 const uint8_t decomposed[3]={'A',0xcc,0x81},composed[2]={0xc3,0x81},invalid[2]={0xc0,0xaf};
 for(int cycle=0;cycle<2;cycle++) {
  assert(!u8_check(decomposed,sizeof(decomposed)));
  size_t size=0;uint8_t *normalized=u8_normalize(UNINORM_NFC,decomposed,sizeof(decomposed),NULL,&size);assert(normalized && size==2 && !memcmp(normalized,composed,2));
  size_t length=0;uint8_t *lower=u8_tolower((const uint8_t*)"AÇÃO",strlen("AÇÃO"),"pt",UNINORM_NFC,NULL,&length);assert(lower && length==strlen("ação") && !memcmp(lower,"ação",length));free(lower);
  /* Reject malformed input with the validation API before normalization. */
  assert(u8_check(invalid,sizeof(invalid))==invalid);
  assert(size==2 && !memcmp(normalized,composed,2));free(normalized);
 }
 puts("{\"UTF8_validation\":true,\"NFC_combining_mark_roundtrip\":true,\"Portuguese_lowercase\":true,\"overlong_UTF8_refused\":true,\"prior_state_preserved\":true,\"lifecycle_cycles\":2}");return 0;
}
