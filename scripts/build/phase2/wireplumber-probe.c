#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <wp/wp.h>

int main(void)
{
    wp_init(WP_INIT_ALL);
    assert(strcmp(wp_get_library_version(), "0.5.15") == 0);
    assert(strcmp(wp_get_library_api_version(), "0.5") == 0);
    WpProperties *props = wp_properties_new("toddy.name", "native", "toddy.policy", "owner", NULL);
    assert(props && wp_properties_get_count(props) == 2);
    assert(strcmp(wp_properties_get(props, "toddy.policy"), "owner") == 0);
    WpProperties *copy = wp_properties_copy(props);
    assert(copy && wp_properties_set(copy, "toddy.policy", "revoked") == 1);
    assert(strcmp(wp_properties_get(props, "toddy.policy"), "owner") == 0);
    assert(strcmp(wp_properties_get(copy, "toddy.policy"), "revoked") == 0);
    assert(wp_properties_get(props, "toddy.absent") == NULL);
    wp_properties_unref(copy);
    wp_properties_unref(props);
    WpCore *core = wp_core_new(NULL, NULL, wp_properties_new("remote.name", "toddy-absent-remote", NULL));
    assert(core && !wp_core_is_connected(core));
    assert(wp_core_get_pw_context(core) != NULL);
    assert(!wp_core_connect(core));
    assert(!wp_core_is_connected(core));
    g_object_unref(core);
    puts("native Wireplumber0.5.15 properties/copy isolation/core lifecycle and absent-remote refusal");
    return 0;
}
