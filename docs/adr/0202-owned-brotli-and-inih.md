# ADR-0202 — Own Brotli and INIh metadata prerequisites

Status: accepted · Date: 2026-11-10 · Story: B02

The initial Exiv20.28.8 local profile omitted optional Brotli/INI support. Real
original regressions exercised those paths, so qualify the frozen recommended
libraries instead of turning their failures into passes. Keep network transports
unselected. Use BLFS13.1-systemd general/brotli.html1.2.0 and general/inih.html62;
official archives matched frozen MD5 before SHA256 freeze/extraction. No foundation
component upgrade or new mandatory external corpus/Python binding is introduced.

Brotli archive SHA256
`816c96e8e8f193b40151dad7e8ff37b1221d019dbcb9c35cd3fadbfe6477dfec`.
Shared common/encoder/decoder and CLI, release/source isolation, all12original
registered tarball C cases passed. The source tarball omits optional downloaded
corpus files; those and Python bindings are unselected, not passes.42compiledELFs/
17stage files; native install/post0/0,35changedpaths/40entries. Installed UID101,
private devices/no route passed actual binary/UTF8 compression and decompression,
compressed integrity, malformed refusal/input retained/two recoveries, shared ABI/
pkg-config/APT0. [Proof](../evidence/B02-brotli-install.json).
Package SHA256 `c693b15ad467bc5cc6d0b77c9c83356073224ea3fad8597424a24666d220cee2`;
raw SHA256 `12bdea69eaaa8cc0db009e7e75233f7ebf33f4274b790328bba87e0975554236`.

INIh archive SHA256
`9c15fa751bb8093d042dae1b9f125eb45198c32c6704cd5481ccde460d4f8151`.
Normalize only source directory inih-r62→inih-62 for the existing preparer; no
source-content change. Select C library and INIReader C++, default bounded stack
parser. All16original Meson programs passed, including original C++ example;
55compiledELFs/six stage files. The own final collector mistakenly expected15,
after compile/originals/stage/consumer had already passed. Metadata-only collect2
corrected the count with registration equality, retained prepared recipe and exact
future two-literal cardinality delta. No compiler/original/consumer replay.
Native install/post0/0,19changedpaths/20entries. Installed UID101/private devices/
no route passed C callback+C++ UTF8 parsing/typed defaults/missing fallback,
malformed refusal/prior state retained/two recoveries/shared ABI/pkg-config/APT0.
No owner config is read or modified. [Proof](../evidence/B02-inih-install.json).
Package SHA256 `32861b494bc443079e69c3846760bcb1f42b5a966831df8c22c93004ff3b3734`;
raw SHA256 `1d9c3ae4f8ce4c545cf031180c48e37438ef2e449fdebd42179798a308dd0968`.

Retain full upstream notices. These library checks do not accept Exiv2,
LocalSearch, browser, GTK widgets or GNOME. Reconfigure Exiv2 only with new real
feature inputs, preserve the failed profile/ELFs/logs, then run the affected
original tests and native parser checks. Do not rebuild/reinstall these accepted
libraries or repeat their unchanged tests.
