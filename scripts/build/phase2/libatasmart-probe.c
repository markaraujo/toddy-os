#include <atasmart.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void require(int condition, const char *message)
{
    if (!condition) {
        fprintf(stderr, "%s\n", message);
        exit(EXIT_FAILURE);
    }
}

static void check_fixture(const char *path, const char *model, SkDisk *disk)
{
    uint32_t storage[512];
    FILE *file = fopen(path, "rb");
    require(file != NULL, "fixture open failed");
    size_t size = fread(storage, 1, sizeof(storage), file);
    require(size == 1572 && feof(file) && !ferror(file), "invalid fixture size");
    require(fclose(file) == 0, "fixture close failed");
    require(sk_disk_set_blob(disk, storage, size) == 0, "valid fixture rejected");

    const SkIdentifyParsedData *identify;
    require(sk_disk_identify_parse(disk, &identify) == 0 &&
            strcmp(identify->model, model) == 0, "wrong ATA model");
    SkBool available;
    const SkSmartParsedData *smart;
    require(sk_disk_smart_is_available(disk, &available) == 0 && available &&
            sk_disk_smart_parse(disk, &smart) == 0 && smart, "SMART parse failed");

    errno = 0;
    require(sk_disk_set_blob(disk, storage, size - 1) == -1 && errno == EINVAL,
            "truncated fixture accepted");
    require(sk_disk_identify_parse(disk, &identify) == 0 &&
            strcmp(identify->model, model) == 0, "failed parse changed ATA model");
    require(sk_disk_set_blob(disk, storage, size) == 0 &&
            sk_disk_smart_parse(disk, &smart) == 0, "valid reload failed");
}

int main(int argc, char **argv)
{
    require(argc == 3, "expected two upstream fixture paths");
    SkDisk *disk = NULL;
    require(sk_disk_open(NULL, &disk) == 0 && disk, "blob context open failed");
    check_fixture(argv[1], "ST9160821AS", disk);
    check_fixture(argv[2], "WDC WD5000AAKS-00TMA0", disk);
    sk_disk_free(disk);
    puts("Two upstream SMART blobs parsed, truncation refused, ATA model retained and valid reload passed");
}
