#define GCR_API_SUBJECT_TO_CHANGE
#define GCK_API_SUBJECT_TO_CHANGE
#include <gcr/gcr-base.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void) {
  const char fixture[]="Toddy public transport fixture";
  for(int cycle=0;cycle<2;cycle++) {
    GcrSecretExchange *a=gcr_secret_exchange_new(NULL),*b=gcr_secret_exchange_new(NULL);
    assert(a && b);
    char *begin=gcr_secret_exchange_begin(a);assert(begin);
    assert(gcr_secret_exchange_receive(b,begin));g_free(begin);
    char *response=gcr_secret_exchange_send(b,fixture,-1);assert(response);
    assert(gcr_secret_exchange_receive(a,response));g_free(response);
    gsize length=0;const char *received=gcr_secret_exchange_get_secret(a,&length);
    assert(received && length==strlen(fixture) && memcmp(received,fixture,length)==0);
    assert(!gcr_secret_exchange_receive(a,"Toddy malformed exchange"));
    received=gcr_secret_exchange_get_secret(a,&length);
    assert(received && length==strlen(fixture) && memcmp(received,fixture,length)==0);
    g_object_unref(a);g_object_unref(b);
  }
  puts("{\"libgcrypt_transport_roundtrip\":true,\"malformed_exchange_refused\":true,\"prior_state_preserved\":true,\"recovery_cycles\":2,\"real_credentials_used\":false}");
  return 0;
}
