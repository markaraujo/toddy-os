# ADR-0022: Refresh two Kbd patch context lines

- Status: Accepted source adaptation; native rebuild/full checks pending
- Date: 2026-11-06
- Scope: Frozen LFS 13.1-systemd Kbd 2.10.0 backspace patch

## Evidence and decision

Strict --fuzz=0 application stopped before configuration/install, changing zero
installed files. Two Turkish keymap hunks still contextualize keycode 15 with
Meta_Tab; the frozen source already uses Backtab. The requested keycode 14
BackSpace-to-Delete change and surrounding mappings remain present exactly.
Book-default GNU Patch applies both hunks with fuzz 2.

Update only those two context lines to Backtab, retaining all requested patch
changes and all source key mappings. Derived patch SHA-256:
19ceb40af281ce8069794514f073e4557898c970c4c80d24db80b2bd3ab3b996.
Independent archive extractions compare book-default and derived zero-fuzz
application. Both exit zero; all 1327 regular postimage files are byte-identical
(excluding patch backup files). Logs and full verification remain outside Git
under .local/logs/h07-kbd-context/. No source version upgrade or new keymap
behavior is introduced beyond the selected book patch.

Preserve the initial failed target tree, freeze the derived input at an
immutable commit URL, rebuild a verified fresh archive and run the complete
suite/native keymap-parser postcheck. Do not apply over a partly patched tree.

## Alternatives and consequences

Accepting default fuzz without validating postimages would weaken the current
strict patch preflight. Skipping the Turkish hunks would produce a different
patch result. Context refresh with measured identical output retains the frozen
book intent and strict matching. Actual keyboard/console integration remains
part of native boot/desktop validation; parser success is not a hardware test.

## Sources

Frozen LFS 13.1-systemd section 8.67, SHA-pinned Kbd archive and backspace patch;
actual keymaps and GNU Patch output from independent verified extractions.
