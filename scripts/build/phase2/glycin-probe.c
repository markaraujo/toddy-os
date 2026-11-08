#include <glycin.h>
#include <assert.h>
int main(void) {
    GBytes *bytes = g_bytes_new_static("pending-native-image-test", 25);
    GlyLoader *loader = gly_loader_new_for_bytes(bytes);
    assert(loader && GLY_IS_LOADER(loader));
    gly_loader_set_sandbox_selector(loader, GLY_SANDBOX_SELECTOR_BWRAP);
    g_object_unref(loader); g_bytes_unref(bytes);
    return 0;
}
