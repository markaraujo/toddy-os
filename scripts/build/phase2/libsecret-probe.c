#include <libsecret/secret.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void) {
  const unsigned char binary[]={0x41,0x00,0xff};
  for(int cycle=0;cycle<2;cycle++) {
    SecretValue *value=secret_value_new((const char*)binary,sizeof binary,"application/octet-stream");
    assert(value);gsize length=0;const char *bytes=secret_value_get(value,&length);
    assert(length==sizeof binary && memcmp(bytes,binary,length)==0);
    assert(secret_value_get_text(value)==NULL);
    SecretValue *ref=secret_value_ref(value);secret_value_unref(value);
    assert(strcmp(secret_value_get_content_type(ref),"application/octet-stream")==0);secret_value_unref(ref);
    SecretSchema *schema=secret_schema_new("org.toddy.PublicFixture",SECRET_SCHEMA_NONE,"owner",SECRET_SCHEMA_ATTRIBUTE_STRING,"generation",SECRET_SCHEMA_ATTRIBUTE_INTEGER,"enabled",SECRET_SCHEMA_ATTRIBUTE_BOOLEAN,NULL);
    assert(schema);
    GHashTable *attributes=secret_attributes_build(schema,"owner","Toddy","generation",42,"enabled",TRUE,NULL);
    assert(attributes && strcmp(g_hash_table_lookup(attributes,"owner"),"Toddy")==0);
    assert(strcmp(g_hash_table_lookup(attributes,"generation"),"42")==0 && strcmp(g_hash_table_lookup(attributes,"enabled"),"true")==0);
    g_hash_table_unref(attributes);secret_schema_unref(schema);
  }
  puts("{\"binary_value_preserved\":true,\"nontext_value_refused_as_text\":true,\"typed_schema_attributes\":true,\"lifecycle_cycles\":2,\"real_credentials_used\":false}");
  return 0;
}
