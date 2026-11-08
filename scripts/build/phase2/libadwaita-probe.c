#include <adwaita.h>

int main(void) {
    g_assert_cmpuint(adw_get_major_version(), ==, ADW_MAJOR_VERSION);
    g_assert_cmpuint(adw_get_minor_version(), ==, ADW_MINOR_VERSION);
    g_assert_cmpuint(adw_get_micro_version(), ==, ADW_MICRO_VERSION);
    return 0;
}
