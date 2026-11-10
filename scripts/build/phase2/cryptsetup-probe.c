#include <libcryptsetup.h>
#include <stdio.h>
#include <string.h>

static int check_header(const char *path, int valid)
{
    struct crypt_device *device = NULL;
    if (crypt_init(&device, path) != 0)
        return 0;
    int result = crypt_load(device, CRYPT_LUKS2, NULL);
    int ok = result < 0;
    if (valid) {
        const char *type = result == 0 ? crypt_get_type(device) : NULL;
        const char *uuid = type ? crypt_get_uuid(device) : NULL;
        ok = type && uuid && strcmp(type, CRYPT_LUKS2) == 0 &&
             strcmp(uuid, "12a3a118-7039-4575-a649-3f559d8d87ee") == 0;
    }
    crypt_free(device);
    return ok;
}

int main(int argc, char **argv)
{
    if (argc != 3)
        return 1;
    for (int i = 0; i < 2; ++i)
        if (!check_header(argv[2], 0) || !check_header(argv[1], 1))
            return 1;
    puts("Cryptsetup LUKS2 metadata refusal and two header reloads passed");
    return 0;
}
