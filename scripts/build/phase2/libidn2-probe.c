#include <idn2.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void) {
 const int flags=IDN2_NONTRANSITIONAL|IDN2_NFC_INPUT;
 const uint8_t invalid[3]={0xc0,0xaf,0};
 assert(idn2_check_version("2.3.8") && !idn2_check_version("99.0"));
 for(int cycle=0;cycle<2;cycle++) {
  uint8_t *ascii=NULL;char *unicode=NULL;
  assert(idn2_lookup_u8((const uint8_t*)"bücher.example",&ascii,flags)==IDN2_OK && ascii && !strcmp((char*)ascii,"xn--bcher-kva.example"));
  assert(idn2_to_unicode_8z8z((const char*)ascii,&unicode,flags)==IDN2_OK && unicode && !strcmp(unicode,"bücher.example"));idn2_free(unicode);idn2_free(ascii);
  ascii=NULL;assert(idn2_lookup_u8((const uint8_t*)"faß.de",&ascii,flags)==IDN2_OK && ascii && !strcmp((char*)ascii,"xn--fa-hia.de"));idn2_free(ascii);
  ascii=NULL;assert(idn2_lookup_u8(invalid,&ascii,flags)==IDN2_ENCODING_ERROR);idn2_free(ascii);
  ascii=NULL;assert(idn2_lookup_u8((const uint8_t*)"-bad.example",&ascii,flags)==IDN2_HYPHEN_STARTEND);idn2_free(ascii);
  ascii=NULL;assert(idn2_lookup_u8((const uint8_t*)"bücher.example",&ascii,flags)==IDN2_OK && !strcmp((char*)ascii,"xn--bcher-kva.example"));idn2_free(ascii);
 }
 puts("{\"UTF8_punycode_roundtrip\":true,\"nontransitional_sharp_s\":true,\"invalid_UTF8_and_leading_hyphen_refused\":true,\"post_refusal_recovery\":true,\"cycles\":2}");return 0;
}
