# ADR-0206 — Owned Aspell English backend and generated Info inventory

Status: accepted; native package/API/CLI qualified, editor/GUI acceptance pending.
Date: 2026-11-10 · Story: B02

Use frozen BLFS13.1-systemd `general/aspell.html`, Aspell0.60.8.2 source SHA256
57fe4863eae6048f72245a8575b44b718fb85ca14b9f8c0afc41b254dfd76919,
matching book MD5. Enchant2.8.19 requires this provider; do not replace it with
an empty backend or broaden the optional provider matrix. Reuse owned Which2.25,
GCC16.2/GLibc2.44/Ncurses6.6, without foundation upgrades.

Use the exact English dictionary linked by the frozen book, official GNU
aspell6-en-2020.12.07-0.tar.bz2 SHA256
4c8f734a28a088b88bb6481fcf972d0b2c3dc8da944f7673283ce487eac49fb3.
The book supplies no dictionary checksum: authenticated GNU HTTPS provenance and
observed SHA frozen before guest use are the trust basis, not a signature claim.
Retain complete original SCOWL/Ispell/WordNet notices and source identity with
all22 compiled dictionary files and aliases. English lexical tests do not imply
Portuguese dictionary support. Native per-file notices retain GPL/LGPL conditions
for Aspell; the inventory uses explicit LicenseRef entries rather than inventing
one license for the entire collection.

Aspell has no upstream test suite in this frozen version. Build optimized C/C++
shared API/CLI out of tree as UID101 with source read-only; never report an
invented original-suite pass. Own actual C API/CLI qualification proves known
words, misspelling and suggestion, UTF8 personal-word persistence across speller
recreation, two session add/clear cycles, malformed dictionary/invalid language/
unknown-option refusal with state retention and two fresh-speller recoveries.
This is basic backend validation, not general dictionary-parser security.

Initial compiler and main staging succeeded. The dictionary branch failed because
our data-dir excluded the charset files. Resume only that branch using the main
staged charset directory plus original dictionary metadata, without extraction,
compiler or main-stage replay. All92 compiled ELF hashes remained identical;
244 regular stage files qualified. The original job exit2 remains retained.

Native installation completed (recipe0/post1,267 changed paths/347 package entries).
The first own postcheck expected an absent setpriv executable before its consumer
started. Keep the installed archive unchanged and set NoNewPrivs through native
Python prctl after UID/GID101 drop. Verify-only returned0/0 with full-root changed0;
installed private-device/no-route API/CLI, all staged bytes, shared ABI and APT0
passed. No reinstall, host installation, privileges weakening or provider/UI claim.

The shared Info index is generated state, not package-owned payload. The existing
native backend registered both manuals and changed `/usr/share/info/dir`, correctly
visible in the full-root manifest. We found its generated_paths metadata omitted
this write when a prebuilt index was absent. Fix future metadata projection using
the same document list as registration; two regressions cover absent-index and
compressed-document cases, with registration behavior unchanged. Reconcile only
the existing Aspell metadata against the original producer hash, archive, verified
transaction and actual before/after index hashes. Preserve original and corrected
records; do not rewrite archive, installed index or payload. This unqualified
transaction retains complete root verification, not optimized-path acceptance.

[Evidence](../evidence/B02-aspell-install.json) binds both raw bundles, source,
original failures, corrected verification, archive and metadata reconciliation.
No Enchant, Libspelling, editor, GUI, Portuguese lexicon or G2 acceptance follows.
Target free space after installation17204727808B is only about23.7MiB above the
16GiB reserve. Before more builds assess qualified duplicate-stage custody using
verified archive/payload evidence; no blind cache deletion, source rebuild or
unchanged trim retry. Continue eligible editor prerequisites; complete all B02,
then stop. LocalSearch native branch remains parked at its existing failure budget.
