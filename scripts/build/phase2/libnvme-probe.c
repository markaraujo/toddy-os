#include <errno.h>
#include <libnvme.h>
#include <libnvme-mi.h>
#include <stdio.h>
#include <string.h>
#include <syslog.h>

int main(void)
{
    const char *expected = "6ba7b810-9dad-11d1-80b4-00c04fd430c8";
    unsigned char bytes[NVME_UUID_LEN];
    char text[37];

    for (int cycle = 0; cycle < 2; ++cycle) {
        if (nvme_uuid_from_string("invalid", bytes) != -EINVAL ||
            nvme_uuid_from_string(expected, bytes) != 0 ||
            nvme_uuid_to_string(bytes, text) != 0 || strcmp(text, expected) != 0)
            return 1;

        nvme_root_t root = nvme_mi_create_root(stderr, LOG_ERR);
        if (!root)
            return 1;
        nvme_mi_free_root(root);
    }

    puts("NVMe UUID refusal and roundtrip with two fresh local MI contexts passed");
    return 0;
}
