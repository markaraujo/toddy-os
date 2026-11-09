/* Real public C embedding and recovery; never a mocked JS/GI adapter. */
#include <stdbool.h>
#include <gjs/gjs.h>

int main(void) {
    GjsContext *context = gjs_context_new();
    g_assert_nonnull(context);
    GError *error = NULL;
    int status = -1;
    const char *script = "const GLib = imports.gi.GLib; "
        "if (!GLib.str_has_prefix('toddy','tod') || 6*7 !== 42) throw Error('native GI');";
    g_assert_true(gjs_context_eval(context, script, -1, "toddy-native", &status, &error));
    g_assert_no_error(error);
    g_assert_cmpint(status, ==, 0);
    g_assert_false(gjs_context_eval(context, "function {", -1, "toddy-invalid", &status, &error));
    g_assert_nonnull(error);
    g_clear_error(&error);
    g_assert_true(gjs_context_eval(context, "if (40+2 !== 42) throw Error('recovery');", -1,
                                   "toddy-recovery", &status, &error));
    g_assert_no_error(error);
    g_assert_cmpint(status, ==, 0);
    g_object_unref(context);
    g_print("GJS native C/JS/GI/refusal/recovery=42\n");
    return 0;
}
