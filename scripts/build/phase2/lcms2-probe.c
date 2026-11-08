#include <lcms2.h>
#include <assert.h>
#include <stdlib.h>
#include <string.h>
int main(void) {
    cmsHPROFILE profile = cmsCreate_sRGBProfile();
    assert(profile);
    cmsUInt32Number bytes = 0;
    assert(cmsSaveProfileToMem(profile, NULL, &bytes) && bytes > 128);
    void *buffer = malloc(bytes); assert(buffer);
    assert(cmsSaveProfileToMem(profile, buffer, &bytes));
    cmsHPROFILE restored = cmsOpenProfileFromMem(buffer, bytes); assert(restored);
    cmsHTRANSFORM transform = cmsCreateTransform(profile, TYPE_RGB_8, restored,
        TYPE_RGB_8, INTENT_RELATIVE_COLORIMETRIC, cmsFLAGS_NOCACHE);
    assert(transform);
    unsigned char input[3] = {0, 32, 64}, output[3] = {0};
    cmsDoTransform(transform, input, output, 1);
    for(int i=0;i<3;i++) assert(abs((int)input[i]-(int)output[i]) <= 1);
    assert(!cmsOpenProfileFromMem("invalid", 7));
    cmsDeleteTransform(transform); cmsCloseProfile(restored);
    cmsCloseProfile(profile); free(buffer);
    return 0;
}
