#include <udisks/udisks.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
    for (int i = 0; i < 2; ++i) {
        UDisksManager *manager = udisks_manager_skeleton_new();
        UDisksBlock *block = udisks_block_skeleton_new();
        udisks_manager_set_version(manager, "2.11.2");
        udisks_block_set_id_usage(block, "filesystem");

        GVariant *properties = g_dbus_interface_skeleton_get_properties(G_DBUS_INTERFACE_SKELETON(block));
        const char *usage = NULL;
        int ok = g_variant_lookup(properties, "IdUsage", "&s", &usage) &&
                 strcmp(usage, "filesystem") == 0 &&
                 strcmp(udisks_manager_get_version(manager), "2.11.2") == 0;
        g_variant_unref(properties);
        g_object_unref(block);
        g_object_unref(manager);
        if (!ok)
            return 1;
    }

    puts("UDisks local D-Bus skeleton properties and two object lifecycles passed");
    return 0;
}
