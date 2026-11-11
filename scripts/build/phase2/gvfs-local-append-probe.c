#include <gio/gio.h>
#include <string.h>

int main(int argc, char **argv)
{
    GError *error = NULL;
    g_assert_cmpint(argc, ==, 2);
    g_assert_true(g_file_set_contents(argv[1], "prior\n", -1, &error));
    g_assert_no_error(error);
    GFile *file = g_file_new_for_path(argv[1]);
    GFileOutputStream *stream = g_file_append_to(file, G_FILE_CREATE_NONE, NULL, &error);
    g_assert_no_error(error);
    g_assert_nonnull(stream);
    goffset initial = g_seekable_tell(G_SEEKABLE(stream));
    g_assert_cmpint(initial, ==, 0);
    gsize written = 0;
    g_assert_true(g_output_stream_write_all(G_OUTPUT_STREAM(stream), "append\n", 7,
                                          &written, NULL, &error));
    g_assert_no_error(error);
    g_assert_cmpuint(written, ==, 7);
    g_assert_true(g_output_stream_close(G_OUTPUT_STREAM(stream), NULL, &error));
    g_assert_no_error(error);
    gchar *contents = NULL;
    gsize length = 0;
    g_assert_true(g_file_get_contents(argv[1], &contents, &length, &error));
    g_assert_no_error(error);
    g_assert_cmpuint(length, ==, 13);
    g_assert_cmpstr(contents, ==, "prior\nappend\n");
    g_print("baseline_local_initial_tell=0 append_preserves_prior_bytes=true length=13\n");
    g_free(contents);
    g_object_unref(stream);
    g_object_unref(file);
    return 0;
}
