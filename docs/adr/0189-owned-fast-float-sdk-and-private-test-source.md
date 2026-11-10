# ADR-0189: Owned Fast_float SDK and immutable private doctest source

Status: header/CMake SDK native package accepted; terminal/UI pending.

Read actual VTE0.84.1 source and frozen BLFS13.1-systemd gnome/vte.html. Freeze its
recommended Fast_float8.2.10 from general/fast_float.html, official archiveSHA256
`76f958dd97b1cf4d8862d1f0986a47d4bdfa8845252bae15ef0f40de3b95961f`.
This is header-only build SDK, not a new running service or required live desktop
payload. No frozen foundation/terminal version upgrade or compiler network fallback.
VTE/fmt/simdutf source leaves are selected separately, not yet functional apps.

The original test CMake downloads an unpinned lemire/doctest fork and optional
supplemental dataset. Resolve the source-selected fork HEAD once to exact commit
`dfb11445b941a75813c26aa9184f08c6ce774615`; pin official HTTPS archiveSHA256
`a31178827d624e0e7c31419f61a3b526cadf2f744c82bc532be9773fd673e090`
before guest use, retain270source file hashes. Publisher signature is not claimed.
Source root rename fast_float→fast-float changes no bytes. Private doctest source
is used through explicit FETCHCONTENT_SOURCE_DIR_DOCTEST with fully disconnected
CMake; no moving compiler download or framework installed into the OS.

Follow the frozen book's installation boundary: configure/install-stage with tests
OFF first, then use a SEPARATE test tree with original tests ON. This prevents the
private test framework's install rules from entering the SDK stage. Optional network
supplemental data and default-off exhaustive sweeps/benchmarks are unselected, never
counted as passes. Source tests/assertions unchanged. Original14core CTest programs
passed with no skipped/error/failure entries;47test-tree ELFs/12regular stage files.
Actual staged CMake exact version discovery and C++ float/double/trailing-input
pointer/invalid input/overflow/two reset-recovery cycles passed.

Owned native package8.2.10toddy1 architectureall, native install/post0/0 changed27paths/
27owned entries, archiveSHA256
`b26c10cf6009e8fd7dd988ecca6712db6af6f7fbf8cf65de2328ab5393c5d6c1`.
Installed UID101 CMake/header consumer passed under private no-route namespace,
package audits0. Architectureall describes header/config data; x86_64 consumer
qualification does not invent other-machine/hardware results. No original replay.
[Exact preparation/private source/originals/native proof](../evidence/B02-fast-float-install.json).

Retain complete Apache2/MIT/Boost alternative license texts and leading installed
header conditions. Private doctest MIT source/license remains in frozen build
inputs/inventory; not installed by this package. Numeric/media/terminal input is
untrusted user-process data, never an administrative permission source. C++ ABI/
compiler baseline remains accepted GCC16.2; this SDK adds no shared runtime ABI.

Next fmt12.2.0 and simdutf9.0.0 actual build/test contracts, then VTE/GNOME Terminal
with real PTY/process/Stop/user-settings/native graphical focus validation. This
SDK alone completes no B02 graphical criterion. Headless native focus remains
parked; use actual virtual seat/input and complete dedicated evidence before
another native gate. Finish all B02 then stop as requested.
