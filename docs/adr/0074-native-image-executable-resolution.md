# ADR-0074: Resolve executable dependencies with the image's own loader

- Date: 2026-11-07
- Status: Native component verified; full foundation assembly pending
- Extends: ADR-0036, ADR-0064 and ADR-0072/0073

## Decision

Add h10/image_runtime.py after whole-tree attribution in the prepared assembler.
Use the verified declarations as the image namespace, including deliberately
generated live scripts. Inspect actual regular files with the source-built
Readelf. For every ELF with PT_INTERP, invoke that exact image interpreter with
--list inside a chroot rooted at the image. Verify every reported provider's
physical type, device, metadata and SHA-256 against the declarations. The kernel
vDSO is separately recognized, never treated as a package-owned file.

Accept only the two measured foundation interpreter paths: Glibc's canonical
/usr/lib/ld-linux-x86-64.so.2 and the owned /lib64 alias resolving to that same
file. Reject changed/unowned libraries, missing interpreters, build-only search
paths, unexpected loader output, preload configuration and ELF audit hooks.
Each inspection has a bounded subprocess timeout and a cleared environment.
The component does not run application entry points to test loadability.

Executable shebangs must resolve to an owned executable inside the image.
Environment dispatch uses the reviewed /usr/bin:/usr/sbin path; only explicit
env -S splits multiple arguments. Relative interpreters, long/truncated lines,
unreviewed env options and missing commands fail. Original source database
consistency remains protected by assembly, and image database bytes must remain
unchanged during this audit. Failures retain the separate runtime report and
prevent assembled=true.

## Experiment and correction

The first actual eleven-package marker/payload fixture was not a runtime closure.
Its Perl could not load libcrypt.so.2, and two OpenSSL scripts lacked env. These
providers are Libxcrypt and Coreutils, already built in the installed target.
H07's prepared metadata closure already includes the Perl edge and derives the
OpenSSL script edge from actual interpreter ownership. Do not rewrite the active
database or pretend that the earlier payload/marker tests proved executability.
The runtime fixture explicitly adds these providers and their real dependencies.

The first comparator also assumed every PT_INTERP used /lib64. Native Readelf
showed Glibc's own utilities use the canonical /usr/lib path. Both resolve to the
same accepted native file. Corrected the exact path policy; did not alter the
binary, loader or package records. Failed fixture and raw diagnostics are retained:
.local/logs/h11-image-key-marker-review-<sha256>.log SHA-256
a65bc87b0a6f903c75626306a8cbf4a50aa427375afa5a1a78f406fd0411c4e8.

Reproduction:

```sh
python3 scripts/host/probe_image_key_marker_review.py --runtime
python3 scripts/host/probe_root_assembly_preflight.py
```

The corrected private root configures seventeen actual native packages. The
complete component pass finds 147 dynamic executable entries and 41 executable
scripts, with zero findings. It records 410 ELF entries without PT_INTERP as
outside standalone executable testing. Libraries actually loaded by the 147
executables are still verified in their measured execution contexts. The
independent payload check verifies 19,926 owned entries.

Eight refusal cases passed: remove the actual OpenSSL shared library (native
loader exit 127), remove the image loader, remove a resolved library's ownership
declaration, target the installed builder instead of an image, remove an
interpreter's execute permission, request a missing absolute interpreter, use a
relative interpreter and use a build-only interpreter. Restoring the fixture
passes a second complete runtime audit. Existing ten payload and nine marker
negative cases also pass, including an actual generated private key. Builder
package status remains unchanged. The successful disposable fixture is removed
only after complete evidence capture.

Successful raw report SHA-256:
85eb59f3151f5d6aed50162437d9e4d53682e8e09e5d10f96bb0080e7bba7553.
Runtime component SHA-256:
7ff1a6afbaee8d060e5cf9590f247e860b082ca8cbd065a22ecfe3fe236705b0.
Assembler SHA-256:
e284e636d17c7248efdfb74e31f7014b6666af0c6e5f765bf336a7d636797b6d.
Actual gate/preflight report SHA-256:
f8d2667da1ca0469dd54f2f3d6754a8fee0bb892adbcc6ea182aec7a34f4e75d.
Both production profiles and six unsafe destinations are refused; actual full
source readiness still stops at the unfinished H07 shared Info-index ownership.

## Sources, alternatives and limits

Re-read frozen LFS 13.1-systemd 8.2 package management and 8.5 Glibc, especially
dynamic-loader configuration. Local chapter08/pkgmgt.html SHA-256:
b2abe59ca6c46887c158dfa6381fd3d34182ae68b262562ee8e5de0895f0e84a;
chapter08/glibc.html:
463fea4974020e9b3f70effb0c7dfd2d8a42d51997b269695a0c786158ad87f2.
Inspected the accepted Glibc 2.44 elf/rtld.c --list branch and output path,
SHA-256 9487f25c0ce2279d2b024e5a12e381f7607fe141869f373c813eb32165c3ae3a.
The existing source/version freeze is unchanged.

Using builder ldd or checking only declared dependency names could conceal a
missing image provider. A hand-written search-path simulator would need to
duplicate loader search and executable context semantics. The actual native
loader supplies that evidence, at the cost of one bounded process per dynamic
executable and repeated provider verification.

This is deliberately not a replacement for native APT/Dpkg version constraints,
direct declared provider checks, shared objects not reached by these executables,
optional dlopen, internal commands/data/plugins, symbol execution, credentials,
licenses or boot. All remain release obligations. The report marks complete
dependency closure false. No full foundation assembly or new-kernel boot has
run; component success does not complete H10 or advance its gate.
Direct loader invocation also does not establish setuid/setgid secure-execution
behavior; privileged program behavior requires its separate guest tests.
