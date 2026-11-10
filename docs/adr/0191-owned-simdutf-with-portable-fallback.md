# ADR-0191: Owned simdutf with portable scalar fallback

Status: current-VM shared/SDK Unicode consumers accepted; terminal/UI pending.

Use frozen BLFS13.1-systemd general/simdutf.html9.0.0 sourceSHA256
`fd2ce975f29809a975a8da8843cfb3a7265af3f71be548f199d23cf65e101764`.
Actual CMake/test/generator source reviewed before preparation. Select shared
library/default original Unicode/base64 tests with FAST_TESTSOFF. Explicitly
include scalar fallback for the portable x86_64 baseline; no march=native or
foundation ABI upgrade. Optional standalone CLI/tools, developer fuzz/internal/
atomic-base64 matrices and benchmarks are unselected, not passes. VTE needs the
library, not these extra CLI programs. No compiler networking/new test framework.

Original91programs passed in67.18s. Their raw output retains79observations that
icelake is unsupported by this VM CPU; that branch is NOT hardware-qualified.
Supported runtime implementations/scalar fallback only; no different-CPU claim.
193compiled ELFs/49regular stage files retained. Actual staged CMake/shared API
Portuguese+emoji UTF8↔UTF16 roundtrip, codepoint/surrogate lengths, overlong UTF8/
unpaired UTF16 refusal and two recovery cycles passed. Source assertions unchanged.

Native install/post0/0 changed83paths/85owned entries, archiveSHA256
`4f68407ccf6c7b4f26514b58a16d27ab211045a5ef9f0b0f2e3cb13cfa61f0d2`.
Actual installed UID101 CMake/shared libsimdutf.so.34/Unicode consumer passed in
private no-route namespace, pkg-config9.0.0/package audits0. Full root verification
retained; no source/compiler/original suite replay or user configuration change.
[Originals, source, unsupported branch and native proof](../evidence/B02-simdutf-install.json).

Retain exact Apache2/MIT alternative texts and leading runtime C++/header conditions.
Malformed terminal/media text is untrusted data in user processes; validation does
not grant privileged executor capabilities. Installed C++ scope does not claim
all unused APIs/architectures or physical hardware tested. No VTE widget/terminal
window/focus/credential/login criterion is completed by this library alone.

Actual VTE0.84.1 preflight now finds all required owned SDKs, including existing
LZ41.10.0/PCRE2-10.49/GTK3/GnuTLS/ICU/Pango/Systemd and new SIMD/format headers.
Select GTK3 API2.91 used by approved GNOME Terminal3.60.0; GTK4 VTE widgets are not
needed by this consumer. Preserve accessibility/FriBidi/ICU/GnuTLS/GI/Systemd.
Read shell hooks before packaging and preserve user prompt settings; real PTY/
Stop/recovery/widget/focus and GNOME Terminal remain separate gates.
