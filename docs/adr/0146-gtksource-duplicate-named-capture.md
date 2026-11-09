# ADR-0146: Resolve GtkSourceView duplicate named captures without changing fixtures

Status: Accepted one-file correction; native diagnosis and affected pure syntax passed, original display driver/product UI pending.
Date: 2026-11-09
Scope: B02 GtkSourceView5.20.0 private PCRE2 wrapper, not the foundation regex ABI.

## Concrete cause

The frozen shell grammar defines HDB in two alternative captures and explicitly
allows duplicate names. Its end expression refers to that matched name.
`impl_match_info_fetch_named_pos()` calls
`pcre2_substring_number_from_name()` and treats every negative return as failure.
The official PCRE2 contract returns PCRE2_ERROR_NOUNIQUESUBSTRING for a duplicate
name, even when one alternative matched. This explains the preserved HDB warning;
it does not explain or waive the separate GDB grammar/invalid-UTF8 failures.

## Proposed limited correction

Keep the original unique-name path. Only on the duplicate-name error, obtain the
name table entries and select the first participating capture. PCRE2 uses this
selection rule for named extraction. Preserve missing-name refusal. The patch
changes only gtksourceview/implregex.c, retains licensing and original test/source
archives, and does not change PCRE2, GLib, grammar fixtures or test assertions.

Before applying this to any package, run a real native consumer against the
original and corrected implementation. It must reproduce the original failure
and verify single/double quote alternatives, empty captured strings, first
participating duplicate selection and missing-name refusal. Then rebuild the
changed package slice and execute affected original regex/shell tests and native
editor behavior. No outcome is accepted by this document alone.

The previous branch was parked after two unsuccessful harness/test-selection
corrections. This new source/API evidence meets its explicit condition for a
narrow diagnostic resumption; it does not reset the persistent attempt ledger
or authorize more unchanged corpus runs. The healthy SpiderMonkey writer must
finish before any guest diagnostic job is dispatched.

## Sources

- Authenticated GtkSourceView5.20.0 source SHA256
  e38bcd23f52b86eadf0fe4d8bde698e3a8ca102322b8b4cf1a51ac294a448c1b,
  data/language-specs/sh.lang and gtksourceview/implregex.c.
- [PCRE2 unique-name API](https://www.pcre.org/current/doc/html/pcre2_substring_number_from_name.html),
  consulted 2026-11-09; explicit duplicate-name error and name-table alternative.
- [PCRE2 name-table API](https://www.pcre.org/current/doc/html/pcre2_substring_nametable_scan.html),
  consulted 2026-11-09; entry length and first/last matching entries.

## Observed native result

[Actual original-vs-corrected probe](../evidence/B02-gtksourceview-duplicate-diagnosis.json)
reproduced five duplicate-name failures in the original implementation; corrected
six cases passed, including the unchanged unique-name control and missing-name
refusal. All230previous compiled artifacts remained unchanged. The package was
then rebuilt/staged from a distinct copied input;765original input files remained
unchanged and exactly one library source file was patched.

[Actual affected verification](../evidence/B02-gtksourceview-patched-stage.json)
passed original Python2/3, shell, JSON and XML syntax cases, with230new compiled
artifacts unchanged after tests. The first original regex driver invocation
aborted before cases because its gtk_test_init requires a display. Preserve that
failure; run this single driver in a fresh native Mutter context. No rebuild,
full corpus retry, original assertion change, installation or editor acceptance.
