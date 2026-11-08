#include <appstream.h>

int main(void) {
    const gchar *xml = "<component type='generic'><id>org.toddy.NativeProbe</id><metadata_license>CC0-1.0</metadata_license><name>Toddy ação 日本語</name><summary>Native metadata probe</summary></component>";
    GError *error = NULL;
    AsMetadata *metadata = as_metadata_new();
    g_assert_true(as_metadata_parse_data(metadata, xml, -1, AS_FORMAT_KIND_XML, &error));
    g_assert_no_error(error);
    AsComponent *component = as_metadata_get_component(metadata);
    g_assert_nonnull(component);
    g_assert_cmpstr(as_component_get_id(component), ==, "org.toddy.NativeProbe");
    g_assert_cmpstr(as_component_get_name(component), ==, "Toddy ação 日本語");
    g_object_unref(metadata);
    metadata = as_metadata_new();
    g_assert_false(as_metadata_parse_data(metadata, "<component><broken></component>", -1, AS_FORMAT_KIND_XML, &error));
    g_assert_nonnull(error); g_clear_error(&error); g_object_unref(metadata);
    return 0;
}
