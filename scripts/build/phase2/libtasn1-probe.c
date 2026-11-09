#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <libtasn1.h>
extern const asn1_static_node toddy_asn1_tab[];
int main(void) {
  asn1_node definitions=NULL,node=NULL,decoded=NULL;
  char error[ASN1_MAX_ERROR_DESCRIPTION_SIZE]={0};
  unsigned char der[64],value[16];
  int length=sizeof der,size;
  assert(strcmp(asn1_check_version(NULL),"4.21.0")==0);
  assert(asn1_array2tree(toddy_asn1_tab,&definitions,error)==ASN1_SUCCESS);
  assert(asn1_create_element(definitions,"Toddy.Envelope",&node)==ASN1_SUCCESS);
  assert(asn1_write_value(node,"number","42",0)==ASN1_SUCCESS);
  assert(asn1_write_value(node,"enabled","TRUE",1)==ASN1_SUCCESS);
  assert(asn1_der_coding(node,"",der,&length,error)==ASN1_SUCCESS);
  const unsigned char expected[]={0x30,0x06,0x02,0x01,0x2a,0x01,0x01,0xff};
  assert(length==(int)sizeof expected && memcmp(der,expected,sizeof expected)==0);
  for(int cycle=0;cycle<2;cycle++) {
    assert(asn1_create_element(definitions,"Toddy.Envelope",&decoded)==ASN1_SUCCESS);
    size=length;
    assert(asn1_der_decoding2(&decoded,der,&size,ASN1_DECODE_FLAG_STRICT_DER,error)==ASN1_SUCCESS);
    size=sizeof value;assert(asn1_read_value(decoded,"number",value,&size)==ASN1_SUCCESS);
    assert(size==1 && value[0]==42);
    assert(asn1_delete_structure(&decoded)==ASN1_SUCCESS);
    assert(asn1_create_element(definitions,"Toddy.Envelope",&decoded)==ASN1_SUCCESS);
    size=length-1;
    assert(asn1_der_decoding2(&decoded,der,&size,ASN1_DECODE_FLAG_STRICT_DER,error)!=ASN1_SUCCESS);
    if(decoded)assert(asn1_delete_structure(&decoded)==ASN1_SUCCESS);
  }
  assert(asn1_delete_structure(&node)==ASN1_SUCCESS);
  assert(asn1_delete_structure(&definitions)==ASN1_SUCCESS);
  puts("{\"version\":\"4.21.0\",\"strict_DER_typed_roundtrip\":true,\"truncated_input_refused\":true,\"recovery_cycles\":2}");
  return 0;
}
