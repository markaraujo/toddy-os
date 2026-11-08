#include <libdisplay-info/info.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(int argc, char **argv) {
    assert(argc == 2);
    unsigned char bytes[4096];
    FILE *file = fopen(argv[1], "rb"); assert(file);
    size_t size = fread(bytes, 1, sizeof(bytes), file);
    assert(size == 256 && !ferror(file) && feof(file)); fclose(file);
    struct di_info *info = di_info_parse_edid(bytes, size); assert(info);
    assert(di_info_get_edid(info));
    assert(strcmp(di_info_get_make(info), "Red Hat, Inc.") == 0);
    di_info_destroy(info);
    unsigned char invalid[128] = {0};
    assert(!di_info_parse_edid(invalid, sizeof(invalid)));
    assert(!di_info_parse_edid(invalid, 1));
    return 0;
}
