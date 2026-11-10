# ADR-0190: Owned fmt shared library for the minimal terminal

Status: selected native shared/SDK consumers accepted; VTE/terminal/UI pending.

Use frozen BLFS13.1-systemd general/fmt.html12.2.0, official archiveSHA256
`8b852bb5aa6e7d8564f9e81394055395dd1d1936d38dfd3a17792a02bebd7af0`.
Actual source/CMake/tests reviewed before preparation. Shared library/OS/Unicode
APIs and original default tests selected. Private bundled GTest comes from the
same authenticated archive, no framework/network download or runtime installation.
Optional docs/CUDA/fuzz/C++ modules and default-off pedantic matrices are not
selected or counted as passes. No baseline/compiler/ABI upgrade.

Original21core CTest programs passed, no nested GTest skips observed.78compiled
ELFs/22regular stage files retained. Actual staged CMake exact discovery and linked
C++ Unicode text/decimal/hex formatting, runtime invalid-format exception refusal
and two recovery cycles passed. Tests/assertions unchanged, no originals replayed.

Native install/post0/0 changed55paths/57owned entries; archiveSHA256
`09e15ff8805f15f6ba1b46feeb3c8d0998a27e1db16b546cc6f3f56ecedbc591`.
Installed UID101 CMake/C++ consumer0 under private no-route namespace, actual
libfmt.so.12 resolution and pkg-config12.2.0/APT0. Package includes shared library,
headers/configuration and the upstream C static API; installed C++ scope does not
claim every unused API/consumer tested. [Actual originals, source and native proof](../evidence/B02-fmt-install.json).

Retain exact root LICENSE/MIT and leading runtime source/header notices. Private
GTest remains source/test evidence only. Source built with accepted GCC16.2 target
baseline; no machine-specific march=native flags. Invalid external text/formatting
stays user-process data, never an administrative permission. No service or global
configuration/policy is changed by this library package.

Next simdutf9.0.0 actual source/tests/reserve preflight and one isolated build,
then VTE0.84.1/GNOME Terminal3.60.0 PTY/Stop/user-settings/native GUI. Headless
focus branch remains parked; new actual virtual seat/input and reliable complete
evidence required. No B02 criterion is completed by formatter libraries alone.
