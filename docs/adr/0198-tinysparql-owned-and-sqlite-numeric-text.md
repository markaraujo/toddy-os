# ADR-0198 — Own Tinysparql and retain exact SQLite numeric-text exceptions

Status: accepted · Date: 2026-11-10 · Story: B02

## Decision and evidence

Use frozen BLFS13.1-systemd `gnome/tinysparql.html`, page SHA256
`fa08a436cc06ef457c93c6857088e1433ec119f12d3e803d14e6bf51ef7e3585`,
and authenticated Tinysparql3.11.1 archive SHA256
`cfd46021ee1514ad435e714f7aa1ec7a787c7f516a94f4c7438897ee3d6eca1e`.
Build production release/debugfalse/testsfalse with ICU/GI/Vala/Soup3 and builtin
modules; omit optional docs/man/stemmer/Avahi/completion. Preserve the unsafe
SQLite version guard and owned foundation SQLite3.53.4; no downgrade or global
rounding/configuration change. Compile original debug-enabled tests separately
from production. Keep all156production ELFs/207debug-test ELFs/105stage files.

Initial build/stage/local RDF UTF8, disk reopen persistence, malformed-query refusal
with retained state and two delete/reset cycles passed.29selected original programs
passed; core sparql aborted at the first of491cases. The frozen book warns of the
SQLite>=3.53.1 failure family. Original source and goldens remain unchanged.

An isolated per-case census of the original unmodified driver measured487passes
and four failures: aggregate-1, aggregate-distinct-1, bind3 and
update/delete-where-query-3. Each is an exact numeric-text golden difference;
qualification verifies the entire diff rows, every per-case log hash, no other
failed/skipped case and unchanged production/debug/stage manifests. Preserve the
initial fail and both own collector failures (optional Meson metadata, then GLib
TAP-comment listing); census4 passed after narrow parser corrections. A collector
exit0 means diagnostic completion, never a claim that all491original cases pass.

The authenticated SQLite3.53.4 documentation archive already frozen for the
foundation documents the inherited3.53.0 default change from15to17significantdigits
in its release notes. [SQLite release notes](https://sqlite.org/releaselog/3_53_4.html)
are primary source/version3.53.4; local archive/page hashes accompany the proof.
A separate production-library C consumer verified exact typed binary64 arithmetic
for10/3,1/42,1/17and4/9 and lossless lexical roundtrip for each. Numeric5passed with
all original manifests unchanged. Accept this narrow compatibility exception for
library packaging; keep all four original cases FAILED in evidence, without
normalizing arbitrary output or rewriting runtime/goldens.17functional programs
remain compiled/deferred per the book's graphical-session requirement, including
the CLI man test with deliberately omitted manuals.

## Native scope, ABI and recovery

Native install/post0/0:130changed paths/280owned entries. Installed UID101 in a
private-device/no-route namespace passed UTF8 RDF/persistence/refusal/reset,
four typed arithmetic/roundtrip cases and separate Tracker3.0/Tsparql3.0 GI local
queries, shared-library/pkg-config/APT closure. Pins include existing owned
GLib2.88.3/ICU78.3/JSON-GLib1.10.8/libxml2-2.15.3/SQLite3.53.4/Soup3.6.6.
Production exports libtinysparql3.0 ABI and legacy tracker-sparql pkg-config/GI
compatibility without replacing another owned library. XML/network consumers
reuse the existing qualified pinned dependencies; full-root transaction and
installed library resolution passed. No network endpoint or portal daemon was
started; no permission/policy or credentials changed. Actual GNOME portal consent,
indexer/files/UI/cancellation/functional tests remain separate required gates.
No full desktop, physical hardware, full-suite or G2 acceptance follows here.

[Proof and immutable raw log inventory](../evidence/B02-tinysparql-install.json).
Package SHA256 `00926d1ffc08af1d8f800512e436f1e9d93e25abcffa3d7773e09e8d9d549094`;
raw evidence SHA256 `3b0226f02e3b0e252a4a6c465fcfed14bd31945f8484930b599ed0f1ad3c5dbc`.
Do not rebuild/reinstall/replay accepted stages. Future failure recovery begins
with actual job/transaction/postcondition inspection. Next B02 leaf is Glycin
GTK4 then Nautilus, with no repeat of unchanged foundation/original suites.
