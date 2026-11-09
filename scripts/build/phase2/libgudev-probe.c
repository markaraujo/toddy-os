#include <assert.h>
#include <gudev/gudev.h>
#include <stdio.h>

int main(void)
{
    GUdevClient *client = g_udev_client_new(NULL);
    assert(client && G_UDEV_IS_CLIENT(client));
    assert(g_udev_client_query_by_sysfs_path(client, "/sys/devices/toddy-nonexistent") == NULL);
    GUdevEnumerator *enumerator = g_udev_enumerator_new(client);
    assert(enumerator && G_UDEV_IS_ENUMERATOR(enumerator));
    assert(g_udev_enumerator_add_match_subsystem(enumerator, "toddy-nonexistent") == enumerator);
    assert(g_udev_enumerator_add_match_property(enumerator, "TODDY_ABSENT", "1") == enumerator);
    assert(g_udev_enumerator_execute(enumerator) == NULL);
    g_object_unref(enumerator);
    g_object_unref(client);
    puts("native GUdev client/enumerator/filter lifecycle and absent-path/subsystem queries; no device detection claim");
    return 0;
}
