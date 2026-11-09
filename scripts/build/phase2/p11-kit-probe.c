#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <p11-kit/uri.h>
int main(void) {
  for(int cycle=0;cycle<2;cycle++) {
    P11KitUri *uri=p11_kit_uri_new();assert(uri);
    assert(p11_kit_uri_parse("pkcs11:token=Toddy%20Test;object=public;type=cert",P11_KIT_URI_FOR_ANY,uri)==P11_KIT_URI_OK);
    assert(!p11_kit_uri_any_unrecognized(uri));
    CK_ATTRIBUTE_PTR attr=p11_kit_uri_get_attribute(uri,CKA_LABEL);assert(attr && attr->ulValueLen==6 && memcmp(attr->pValue,"public",6)==0);
    char *formatted=NULL;assert(p11_kit_uri_format(uri,P11_KIT_URI_FOR_ANY,&formatted)==P11_KIT_URI_OK && formatted);
    assert(strstr(formatted,"token=Toddy%20Test") && strstr(formatted,"object=public"));free(formatted);
    assert(p11_kit_uri_parse("https:token=bad",P11_KIT_URI_FOR_ANY,uri)==P11_KIT_URI_BAD_SCHEME);
    assert(p11_kit_uri_parse("pkcs11:token=%GG",P11_KIT_URI_FOR_ANY,uri)==P11_KIT_URI_BAD_ENCODING);
    assert(p11_kit_uri_parse("pkcs11:token=recovered",P11_KIT_URI_FOR_ANY,uri)==P11_KIT_URI_OK);
    p11_kit_uri_free(uri);
  }
  puts("{\"typed_PKCS11_URI_roundtrip\":true,\"bad_scheme_and_encoding_refused\":true,\"recovery_cycles\":2,\"credentials_loaded\":false}");
  return 0;
}
