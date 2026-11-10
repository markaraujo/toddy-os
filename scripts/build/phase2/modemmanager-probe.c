#include <libmm-glib.h>
#include <stdio.h>

int main(void) {
    for (unsigned int cycle = 0; cycle < 2; cycle++) {
        MMSimpleConnectProperties *p = mm_simple_connect_properties_new();
        g_assert_nonnull(p);
        mm_simple_connect_properties_set_apn(p, "offline.example");
        mm_simple_connect_properties_set_user(p, "usuário-local");
        mm_simple_connect_properties_set_allow_roaming(p, FALSE);
        mm_simple_connect_properties_set_ip_type(p, MM_BEARER_IP_FAMILY_IPV4V6);
        g_assert_cmpstr(mm_simple_connect_properties_get_apn(p), ==, "offline.example");
        g_assert_cmpstr(mm_simple_connect_properties_get_user(p), ==, "usuário-local");
        g_assert_false(mm_simple_connect_properties_get_allow_roaming(p));
        g_assert_cmpint(mm_simple_connect_properties_get_ip_type(p), ==, MM_BEARER_IP_FAMILY_IPV4V6);
        mm_simple_connect_properties_set_apn(p, NULL);
        mm_simple_connect_properties_set_user(p, NULL);
        g_assert_null(mm_simple_connect_properties_get_apn(p));
        g_assert_null(mm_simple_connect_properties_get_user(p));
        g_object_unref(p);
    }
    puts("MM local C Unicode properties/reset/two fresh cycles; no credentials/device/service access");
    return 0;
}
