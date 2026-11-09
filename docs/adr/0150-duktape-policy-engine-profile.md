# ADR-0150: Qualify frozen Duktape with bytecode APIs unavailable

- Date: 2026-11-09
- Status: Accepted native library profile; Polkit authorization remains pending

Polkit127 requires Duktape2.7.0 in frozen BLFS13.1 general/duktape.html (page
SHA256a0d9eeb076b2d31ce0435c56b7b179ba1cdf27fb4adb0e0bbbfe69c82b3db1f4).
Official HTTPS archive matched the frozen book MD5; its SHA256 is
90f8d2fa8b5567c6899830ddef2c03f3c27960b11aca222fa17aa7ac613c2890.
The release contains no tests directory; do not invent an original full suite.

The [original bytecode-loader report](https://github.com/hmKunlun/compileOOB/blob/main/api_bytecode.md)
shows bounds enforced by release-disabled assertions. The frozen source's own
loader explicitly requires valid trusted bytecode. Use the supported2.7 option
DUK_USE_BYTECODE_DUMP_SUPPORT=false for both normal/debug libraries and their
installed generated header. Its config/config-options YAML documents this option;
its source implements explicit unsupported errors for both load/dump APIs.
The selected authenticated Polkit127 Duktape authority calls no bytecode APIs:
it evaluates policy JavaScript through the normal interpreter. This is a scoped
feature choice, not a silent source-version upgrade or a claim that all engine
vulnerabilities are resolved.

Keep pristine source read-only; copy only build inputs into private compiler
output, change the generated header there and apply the book's -Os→-O2 choice.
Use the supported Makefile LDFLAGS to retain libm in the shared-library dependency
closure, then restore as-needed for subsequent compiler runtime inputs. Native
checks must prove actual DT_NEEDED libm/libc, normal/debug policy evaluation,
strict host callback types, Unicode/JSON/typed arrays/GC, syntax/data refusals,
unsupported bytecode load/dump and heap recovery. Compile/run the unchanged
upstream hello example against both libraries. No full ECMAScript conformance or
Polkit authorization acceptance follows from these library checks.

New Polkit privileged consumers retain a separate mandatory security/ABI review,
including [upstream issue701](https://github.com/polkit-org/polkit/issues/701)
about silently ignored malformed process-subject fields. Do not infer that its
absence of a released fix permits unsafe fallback, or treat untrusted D-Bus data
as a grant. Preserve source version127 while assessing a narrow tested correction.

Actual source build/stage and owned2.7.0-1+toddy1 install/post passed0/0
(29payload entries, archive SHA256
659d3746433ca265e1c46e0b135c1ac19624ac7ad7152cf4d5977a2132fa14b1).
Both libraries passed15native profile checks plus the unchanged upstream hello
example. Actual installed normal/debug consumers each repeated only their
affected15checks, including unsupported bytecode APIs and heap recovery.
Full-root transaction/Dpkg/APT checks passed.
[Evidence](../evidence/B02-duktape-install.json). Polkit daemon, native original
authorization tests and graphical permission UI remain unqualified.
