#include <nettle/sha2.h>
#include <nettle/ecc.h>
#include <nettle/ecc-curve.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void) {
 const unsigned char expected[32]={0xba,0x78,0x16,0xbf,0x8f,0x01,0xcf,0xea,0x41,0x41,0x40,0xde,0x5d,0xae,0x22,0x23,0xb0,0x03,0x61,0xa3,0x96,0x17,0x7a,0x9c,0xb4,0x10,0xff,0x61,0xf2,0x00,0x15,0xad};
 for(int cycle=0;cycle<2;cycle++) {
  struct sha256_ctx hash;unsigned char output[32];sha256_init(&hash);sha256_update(&hash,3,(const unsigned char*)"abc");sha256_digest(&hash,output);assert(!memcmp(output,expected,32));
  const struct ecc_curve *curve=nettle_get_secp_256r1();assert(curve);
  struct ecc_scalar scalar;struct ecc_point point;ecc_scalar_init(&scalar,curve);ecc_point_init(&point,curve);
  mpz_t one,x,y,gx,gy;mpz_inits(one,x,y,gx,gy,NULL);mpz_set_ui(one,1);
  /* Public standard P-256 generator coordinates, not a credential. */
  assert(mpz_set_str(gx,"6b17d1f2e12c4247f8bce6e563a440f2" "77037d812deb33a0f4a13945d898c296",16)==0);
  assert(mpz_set_str(gy,"4fe342e2fe1a7f9b8ee7eb4a7c0f9e16" "2bce33576b315ececbb6406837bf51f5",16)==0);
  assert(ecc_scalar_set(&scalar,one));ecc_point_mul_g(&point,&scalar);ecc_point_get(&point,x,y);assert(!mpz_cmp(x,gx) && !mpz_cmp(y,gy));
  mpz_set_ui(one,0);assert(!ecc_scalar_set(&scalar,one));mpz_set_ui(x,0);mpz_set_ui(y,0);assert(!ecc_point_set(&point,x,y));
  mpz_set_ui(one,1);assert(ecc_scalar_set(&scalar,one));ecc_point_mul_g(&point,&scalar);ecc_point_get(&point,x,y);assert(!mpz_cmp(x,gx) && !mpz_cmp(y,gy));
  mpz_clears(one,x,y,gx,gy,NULL);ecc_point_clear(&point);ecc_scalar_clear(&scalar);
 }
 puts("{\"SHA256_known_answer\":true,\"Hogweed_P256_generator_known_answer\":true,\"zero_scalar_and_off_curve_point_refused\":true,\"post_refusal_recovery\":true,\"lifecycle_cycles\":2}");return 0;
}
