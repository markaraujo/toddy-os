#include <xmlb.h>
#include <string.h>

int main(void) {
    GError *error = NULL;
    XbSilo *silo = xb_silo_new_from_xml("<catalog><item id='toddy'>ação 日本語</item></catalog>", &error);
    g_assert_no_error(error); g_assert_nonnull(silo);
    XbNode *node = xb_silo_query_first(silo, "catalog/item[@id='toddy']", &error);
    g_assert_no_error(error); g_assert_nonnull(node);
    g_assert_cmpstr(xb_node_get_text(node), ==, "ação 日本語");
    g_object_unref(node); g_object_unref(silo);
    silo = xb_silo_new_from_xml("<catalog><item></catalog>", &error);
    g_assert_null(silo); g_assert_nonnull(error); g_clear_error(&error);
    return 0;
}
