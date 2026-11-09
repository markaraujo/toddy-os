#include <gnutls/gnutls.h>
#include <gnutls/crypto.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void) {
 const unsigned char expected[32]={0xba,0x78,0x16,0xbf,0x8f,0x01,0xcf,0xea,0x41,0x41,0x40,0xde,0x5d,0xae,0x22,0x23,0xb0,0x03,0x61,0xa3,0x96,0x17,0x7a,0x9c,0xb4,0x10,0xff,0x61,0xf2,0x00,0x15,0xad};
 const unsigned char decomposed[3]={'A',0xcc,0x81},composed[2]={0xc3,0x81},bad_utf8[2]={0xc0,0xaf};
 assert(gnutls_check_version("3.8.13") && !gnutls_check_version("99.0"));
 for(int cycle=0;cycle<2;cycle++) {
  assert(gnutls_global_init()==0);unsigned char hash[32];assert(gnutls_hash_fast(GNUTLS_DIG_SHA256,"abc",3,hash)==0 && !memcmp(hash,expected,32));
  gnutls_datum_t normal={0},bad={0},domain={0};assert(gnutls_utf8_password_normalize(decomposed,3,&normal,0)==0 && normal.size==2 && !memcmp(normal.data,composed,2));
  assert(gnutls_utf8_password_normalize(bad_utf8,2,&bad,0)==GNUTLS_E_INVALID_UTF8_STRING && bad.data==NULL);
  assert(normal.size==2 && !memcmp(normal.data,composed,2));gnutls_free(normal.data);
  assert(gnutls_idna_map("bücher.example",strlen("bücher.example"),&domain,GNUTLS_IDNA_FORCE_2008)==0 && domain.size==strlen("xn--bcher-kva.example") && !memcmp(domain.data,"xn--bcher-kva.example",domain.size));gnutls_free(domain.data);
  gnutls_priority_t priority=NULL;const char *position=NULL;
  assert(gnutls_priority_init(&priority,"NORMAL:-VERS-ALL:+VERS-TLS1.3",&position)==0);gnutls_priority_deinit(priority);priority=NULL;
  assert(gnutls_priority_init(&priority,"TODDY_INVALID_PRIORITY",&position)<0 && position!=NULL);
  unsigned char material[16],nonce[12],ciphertext[64],plain[9]="Toddy OS",decoded[64];
  for(unsigned n=0;n<sizeof(material);n++)material[n]=(unsigned char)n;
  for(unsigned n=0;n<sizeof(nonce);n++)nonce[n]=(unsigned char)(n+cycle);
  gnutls_datum_t key={material,sizeof(material)};gnutls_aead_cipher_hd_t handle;assert(gnutls_aead_cipher_init(&handle,GNUTLS_CIPHER_AES_128_GCM,&key)==0);
  size_t size=sizeof(ciphertext),count=sizeof(decoded);assert(gnutls_aead_cipher_encrypt(handle,nonce,sizeof(nonce),NULL,0,16,plain,sizeof(plain),ciphertext,&size)==0 && size==sizeof(plain)+16);
  assert(gnutls_aead_cipher_decrypt(handle,nonce,sizeof(nonce),NULL,0,16,ciphertext,size,decoded,&count)==0 && count==sizeof(plain) && !memcmp(plain,decoded,count));
  ciphertext[size-1]^=1;count=sizeof(decoded);assert(gnutls_aead_cipher_decrypt(handle,nonce,sizeof(nonce),NULL,0,16,ciphertext,size,decoded,&count)==GNUTLS_E_DECRYPTION_FAILED);
  ciphertext[size-1]^=1;count=sizeof(decoded);assert(gnutls_aead_cipher_decrypt(handle,nonce,sizeof(nonce),NULL,0,16,ciphertext,size,decoded,&count)==0 && count==sizeof(plain) && !memcmp(plain,decoded,count));
  gnutls_aead_cipher_deinit(handle);gnutls_global_deinit();
 }
 puts("{\"SHA256_and_AEAD_roundtrip\":true,\"tampered_tag_refused_and_recovered\":true,\"actual_password_API_invalid_UTF8_refused\":true,\"NFC_prior_state_preserved\":true,\"IDNA2008_conversion\":true,\"TLS13_priority_and_invalid_priority_refusal\":true,\"lifecycle_cycles\":2,\"real_credentials_used\":false}");return 0;
}
