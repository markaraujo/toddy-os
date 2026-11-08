/* Native in-memory APIs and invalid-FD refusal; no DRM device mutation. */
#include <assert.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <xf86drm.h>
#include <xf86drmMode.h>
#include <drm_fourcc.h>
int main(void) {
    int fixture=42; void *value=NULL; void *table=drmHashCreate(); assert(table);
    assert(drmHashInsert(table,7,&fixture)==0);
    assert(drmHashLookup(table,7,&value)==0 && value==&fixture);
    assert(drmHashDelete(table,7)==0 && drmHashLookup(table,7,&value)==1);
    assert(drmHashDestroy(table)==0);
    char *format=drmGetFormatName(DRM_FORMAT_XRGB8888);
    assert(format && strstr(format,"XR24")); free(format);
    char *modifier=drmGetFormatModifierName(DRM_FORMAT_MOD_LINEAR);
    assert(modifier && strcmp(modifier,"LINEAR")==0); free(modifier);
    errno=0; assert(drmModeGetResources(-1)==NULL && errno==EBADF);
    puts("native-drm-hash-format-modifier-invalid-fd");
    return 0;
}
