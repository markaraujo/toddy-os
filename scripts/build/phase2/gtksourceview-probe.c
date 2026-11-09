/* Headless ABI/data consumer; display/widget qualification is separate. */
#include <gtksourceview/gtksource.h>
#include <string.h>
int main(void) {
    g_assert_cmpint(gtk_source_get_major_version(), ==, 5);
    g_assert_cmpint(gtk_source_get_minor_version(), ==, 20);
    g_assert_cmpint(gtk_source_get_micro_version(), ==, 0);
    gtk_source_init();
    const GtkSourceEncoding *encoding = gtk_source_encoding_get_from_charset("UTF-8");
    g_assert_nonnull(encoding);
    g_assert_cmpstr(gtk_source_encoding_get_charset(encoding), ==, "UTF-8");
    g_assert_null(gtk_source_encoding_get_from_charset("TODDY-INVALID-ENCODING"));
    GtkSourceLanguageManager *manager = gtk_source_language_manager_new();
    GtkSourceLanguage *language = gtk_source_language_manager_get_language(manager, "python3");
    g_assert_nonnull(language);
    g_assert_cmpstr(gtk_source_language_get_id(language), ==, "python3");
    g_assert_null(gtk_source_language_manager_get_language(manager, "toddy-invalid-language"));
    g_object_unref(manager);
    g_print("GtkSourceView5.20.0 native encoding/language data/refusal passed\n");
    return 0;
}
