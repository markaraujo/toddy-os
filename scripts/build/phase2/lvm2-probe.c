#include <libdevmapper.h>
#include <string.h>

int main(void)
{
    for (int i = 0; i < 2; ++i) {
        struct dm_pool *pool = dm_pool_create("toddy-local-lvm-probe", 1024);
        char *group = NULL, *volume = NULL, *layer = NULL;
        if (!pool)
            return 1;
        int ok = dm_split_lvm_name(pool, "vg--local-lv--test-real", &group, &volume, &layer)
                 && group && volume && layer && strcmp(group, "vg-local") == 0
                 && strcmp(volume, "lv-test") == 0 && strcmp(layer, "real") == 0;
        dm_pool_destroy(pool);
        if (!ok)
            return 1;
    }
    return 0;
}
