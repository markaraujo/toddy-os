/* Reproduce named alternative captures used by shell here-doc highlighting. */
#include <glib.h>
#include <stdio.h>
#include <string.h>
#include "implregex-private.h"

static gboolean check(const char *pattern, const char *text, const char *expected) {
  GError *error = NULL;
  ImplMatchInfo *match = NULL;
  ImplRegex *regex = impl_regex_new(pattern, G_REGEX_DUPNAMES, 0, &error);
  g_assert_no_error(error);
  g_assert_nonnull(regex);
  g_assert_true(impl_regex_match(regex, text, 0, &match));
  char *value = impl_match_info_fetch_named(match, "HDB");
  gboolean ok = value && strcmp(value, expected) == 0;
  char *missing = impl_match_info_fetch_named(match, "DOES_NOT_EXIST");
  g_assert_null(missing);
  printf("%s: expected=[%s] actual=[%s]\n", ok ? "PASS" : "FAIL", expected,
         value ? value : "NULL");
  g_free(value);
  impl_match_info_free(match);
  impl_regex_unref(regex);
  return ok;
}

int main(void) {
  unsigned failed = 0;
  failed += !check("^(?P<HDB>END)$", "END", "END");
  const char *pattern = "^(?:'(?P<HDB>[^']*)'|\"(?P<HDB>[^\"]*)\")$";
  failed += !check(pattern, "'EOF'", "EOF");
  failed += !check(pattern, "\"END\"", "END");
  failed += !check(pattern, "''", "");
  failed += !check(pattern, "\"\"", "");
  failed += !check("^(?P<HDB>a)(?P<HDB>b)$", "ab", "a");
  printf("cases=6 failed=%u; missing-name refusal checked each time\n", failed);
  return failed ? 2 : 0;
}
