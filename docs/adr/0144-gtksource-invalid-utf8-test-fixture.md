# ADR-0144 — Preserve the invalid GtkSourceView syntax fixture refusal

Status: accepted technical validation scope; native remaining cases still pending.

## Observed input and behavior

Frozen GtkSourceView5.20.0 source SHA256
e38bcd23f52b86eadf0fe4d8bde698e3a8ca102322b8b4cf1a51ac294a448c1b contains98
syntax fixtures. Exactly one, tests/syntax-highlighting/file.cir (4213bytes,
SHA256723dc8e309adae5b278371ffa43585cf55be329d721a87f11861144ad11f8fc4),
fails strict UTF8 decoding at byte2851 (0xb5).

The first original native driver skipped all98 because its G_TEST_SRCDIR/data
path points beneath testsuite. A private layout linking exact original data fixed
that path. Native context3 then completed9 original cases and aborted on file.cir:
gtk_text_buffer_emit_insert rejected invalid UTF8 through its existing validation.
Original exit-6 and compositor wrapper1 are retained; no passed full driver claim.

## Decision

Do not weaken GTK validation, modify library/test assertions, convert the original
fixture or claim the failed aggregate passed. Reuse the9 completed cases and
run only the88 remaining valid UTF8 fixtures through original binary -p selections.
Retain the malformed fixture's observed refusal separately. Keep18 pre-existing
upstream language-spec SKIPs explicit. Promotion requires the actual selected
results, unchanged binaries/source data and installed ABI/data consumers.

This is a bounded original-corpus exception, not editor UI acceptance, a universal
text-decoding guarantee or permission to bypass a basic desktop/security failure.
The real editor must still open/save normal text and show actual decode failures.

## Recovery

Full original98-fixture source and failed native report remain available. A fixed
upstream fixture/test or an explicit compatible input-policy change invalidates
this exception and requires directly affected checks. Never replay old disposable
VM overlays against changed parent disks.
