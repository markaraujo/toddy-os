/* Actual Unicode normalization, locale collation and malformed UTF8 refusal. */
#include <unicode/uversion.h>
#include <unicode/ustring.h>
#include <unicode/unorm2.h>
#include <unicode/ucol.h>
#include <assert.h>
#include <stdio.h>
int main(void) {
    UVersionInfo version;u_getVersion(version);
    assert(version[0]==78 && version[1]==3);
    UErrorCode error=U_ZERO_ERROR;
    const UNormalizer2 *normalizer=unorm2_getNFCInstance(&error);
    assert(U_SUCCESS(error) && normalizer);
    const UChar decomposed[]={0x63,0x61,0x66,0x65,0x301};UChar normalized[16];
    int32_t count=unorm2_normalize(normalizer,decomposed,5,normalized,16,&error);
    assert(U_SUCCESS(error) && count==4 && normalized[3]==0xe9);
    UCollator *collator=ucol_open("pt_BR",&error);
    assert(U_SUCCESS(error) && collator);
    const UChar first[]={0x61,0xe7,0xe3,0x6f},second[]={0x62,0x61,0x6e,0x61,0x6e,0x61};
    assert(ucol_strcoll(collator,first,4,second,6)==UCOL_LESS);ucol_close(collator);
    error=U_ZERO_ERROR;int32_t length=0;
    u_strFromUTF8(normalized,16,&length,"\xff",1,&error);
    assert(error==U_INVALID_CHAR_FOUND);
    puts("ICU78.3 NFC Portuguese collation and invalid UTF8 refusal passed");
    return 0;
}
