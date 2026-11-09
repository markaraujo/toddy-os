#include <assert.h>
#include <colord.h>
#include <stdio.h>
int main(void) {
    GError *error=NULL;CdIcc *icc=cd_icc_new();assert(icc);
    assert(cd_icc_create_default(icc,&error) && !error);
    assert(cd_icc_get_colorspace(icc)==CD_COLORSPACE_RGB);
    GBytes *bytes=cd_icc_save_data(icc,CD_ICC_SAVE_FLAGS_NONE,&error);assert(bytes && !error);
    gsize size;const guint8 *data=g_bytes_get_data(bytes,&size);assert(size>128);
    CdIcc *loaded=cd_icc_new();assert(cd_icc_load_data(loaded,data,size,CD_ICC_LOAD_FLAGS_NONE,&error) && !error);
    assert(cd_icc_get_colorspace(loaded)==CD_COLORSPACE_RGB);
    CdIcc *bad=cd_icc_new();const guint8 invalid[]={0,1,2,3};assert(!cd_icc_load_data(bad,invalid,sizeof(invalid),CD_ICC_LOAD_FLAGS_NONE,&error) && error);
    g_clear_error(&error);g_object_unref(bad);g_object_unref(loaded);g_bytes_unref(bytes);g_object_unref(icc);
    CdClient *client=cd_client_new();assert(CD_IS_CLIENT(client));g_object_unref(client);
    puts("native Colord default RGB ICC serialize/reopen, client lifecycle and malformed-profile refusal; no color service/device acceptance");return 0;
}
