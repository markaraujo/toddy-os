#include <colord-gtk.h>
#include <stdio.h>

int main(void) {
    for (unsigned int cycle = 0; cycle < 2; cycle++) {
        CdWindow *window = cd_window_new();
        g_assert_true(CD_IS_WINDOW(window));
        g_assert_null(cd_window_get_last_profile(window));
        g_assert_cmpuint(g_signal_lookup("changed", G_OBJECT_TYPE(window)), >, 0);
        g_assert_cmpuint(cd_window_error_quark(), >, 0);
        g_object_unref(window);
    }
    puts("Colord GTK local GObject/profile-empty state/two fresh cycles; no widget/display/service access");
    return 0;
}
