#include <assert.h>
#include <libwacom/libwacom.h>
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv)
{
    WacomDeviceDatabase *db = argc == 2 ? libwacom_database_new_for_path(argv[1]) : libwacom_database_new();
    WacomError *error = libwacom_error_new();
    assert(db && error);
    WacomDevice *device = libwacom_new_from_usbid(db, 0x056a, 0x034f, error);
    assert(device);
    assert(libwacom_get_vendor_id(device) == 0x056a && libwacom_get_product_id(device) == 0x034f);
    assert(strstr(libwacom_get_name(device), "Cintiq"));
    libwacom_destroy(device);
    assert(libwacom_new_from_usbid(db, 0xffff, 0xffff, error) == NULL);
    assert(libwacom_error_get_code(error) != WERROR_NONE);
    libwacom_error_free(&error);
    libwacom_database_unref(db);
    puts("native libwacom Cintiq database lookup/IDs/cleanup and unknown-model refusal; no physical tablet acceptance");
    return 0;
}
