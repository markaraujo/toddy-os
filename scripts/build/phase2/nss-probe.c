#include <nss.h>
#include <pk11pub.h>
#include <secitem.h>
#include <secoid.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void) {
 const unsigned char expected[32]={0xba,0x78,0x16,0xbf,0x8f,0x01,0xcf,0xea,0x41,0x41,0x40,0xde,0x5d,0xae,0x22,0x23,0xb0,0x03,0x61,0xa3,0x96,0x17,0x7a,0x9c,0xb4,0x10,0xff,0x61,0xf2,0x00,0x15,0xad};
 assert(NSS_VersionCheck("3.126") && !NSS_VersionCheck("99.0"));
 for(int cycle=0;cycle<2;cycle++) {
  assert(NSS_NoDB_Init(NULL)==SECSuccess);
  unsigned char hash[32];assert(PK11_HashBuf(SEC_OID_SHA256,hash,(const unsigned char*)"abc",3)==SECSuccess && !memcmp(hash,expected,32));
  unsigned char random[32]={0},zero[32]={0};assert(PK11_GenerateRandom(random,sizeof(random))==SECSuccess && memcmp(random,zero,32));
  /* Public synthetic test material only; no owner key or credential. */
  unsigned char material[16],iv[12],plain[9]="Toddy OS",encrypted[64],decoded[64];
  for(unsigned int n=0;n<sizeof(material);n++)material[n]=(unsigned char)n;
  for(unsigned int n=0;n<sizeof(iv);n++)iv[n]=(unsigned char)(n+cycle);
  PK11SlotInfo *slot=PK11_GetInternalSlot();assert(slot);
  SECItem keyitem={siBuffer,material,sizeof(material)};
  PK11SymKey *key=PK11_ImportSymKeyWithFlags(slot,CKM_AES_GCM,PK11_OriginUnwrap,CKA_ENCRYPT,&keyitem,CKF_ENCRYPT|CKF_DECRYPT,PR_FALSE,NULL);assert(key);
  CK_NSS_GCM_PARAMS gcm={iv,sizeof(iv),NULL,0,128};SECItem params={siBuffer,(unsigned char*)&gcm,sizeof(gcm)};
  unsigned int size=0,count=0;assert(PK11_Encrypt(key,CKM_AES_GCM,&params,encrypted,&size,sizeof(encrypted),plain,sizeof(plain))==SECSuccess && size==sizeof(plain)+16);
  assert(PK11_Decrypt(key,CKM_AES_GCM,&params,decoded,&count,sizeof(decoded),encrypted,size)==SECSuccess && count==sizeof(plain) && !memcmp(decoded,plain,sizeof(plain)));
  encrypted[size-1]^=1;assert(PK11_Decrypt(key,CKM_AES_GCM,&params,decoded,&count,sizeof(decoded),encrypted,size)==SECFailure);
  encrypted[size-1]^=1;assert(PK11_Decrypt(key,CKM_AES_GCM,&params,decoded,&count,sizeof(decoded),encrypted,size)==SECSuccess && count==sizeof(plain) && !memcmp(decoded,plain,sizeof(plain)));
  PK11_FreeSymKey(key);PK11_FreeSlot(slot);assert(NSS_Shutdown()==SECSuccess);
 }
 puts("{\"SHA256_known_answer\":true,\"native_random_bytes\":true,\"AES_GCM_roundtrip\":true,\"tampered_tag_refused\":true,\"post_refusal_recovery\":true,\"init_shutdown_cycles\":2,\"real_credentials_used\":false}");return 0;
}
