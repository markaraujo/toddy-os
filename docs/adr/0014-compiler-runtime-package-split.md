# ADR-0014: Separate native compiler and runtime ownership

Date: 2026-11-06. Status: accepted packaging design; actual install validation pending.

## Evidence and decision

Actual target readelf inspection shows Ninja needs libstdc++.so.6 and
libgcc_s.so.1; libgmpxx likewise needs libstdc++.so.6. These are presently
provided by temporary toolchain files and must receive final native ownership.
Do not make every C++ application depend on the complete compiler payload.

After the complete final GCC 16.2.0 suite is accepted, stage the book install
unchanged, then split root /usr/lib versioned shared runtimes into gcc-runtime.
Keep compiler executables, headers, static/development libraries, unversioned
linker aliases and compiler-specific plugins in gcc. Both components retain
corresponding source/recipe provenance and upstream notices. gcc depends on
its exact runtime package version plus its actual math/compression providers.

Splitting renames staged files without changing bytes, modes or aliases.
Preflight requires core runtime files, regular copyright data, ELF payloads
and library-local symlink targets. Reject an existing partial runtime stage,
non-ELF candidates, special files or escaping/missing aliases before mutation.
Unit fixtures exercise byte/alias preservation and preflight rejection; these
are not represented as a tested installed compiler. Actual stage inspection,
package installation and native C/C++/thread/linker postchecks remain required.

## Alternatives and consequences

One monolithic GCC package would own the files, but overcouple application
runtime dependency closure to the compiler. Symlinking to the temporary
compiler directories would conceal incomplete native ownership and is rejected.
This split stays within ADR-0008's source-built .deb policy and uses no foreign
binary package or new packaging framework.

The final dependency audit must add gcc-runtime to actual consumers, including
already-built C++ packages, using versioned native metadata updates with
preserved prior archives. Audit optional unwinder use and the mandatory base
profile explicitly; absence of DT_NEEDED alone does not prove optional dynamic
loading is unused. Do not declare runtime/dependency closure complete yet.
No tested source tree or original critical-test evidence is removed by this
packaging operation. Preserve a cold tested-GCC checkpoint before installing.

Sources: frozen LFS 13.1-systemd 8.32 installation/ownership/alias instructions;
actual Ninja and libgmpxx readelf output in the disposable target; staged
packaging behavior defined in scripts/build/h07/split-gcc-runtime.py.

Read-only native compiler/ELF inventory against the 101-package root measured
GCC defaults -march=x86-64 and -mtune=generic. Of 2551 ELFs, 1025 declare only
x86-64-baseline ISA-needed notes; 1526 have no such note. Absent notes do not
prove instruction-level compatibility, and runtime-dispatched code needs its
source context. H12 must still exercise the declared boot CPU profile.
Use native Binutils 2.47 for this inspection: builder 2.42 returns exit 1 on
Glibc crt1.o notes while native readelf reads the same object with exit 0.
Raw .local/logs/h07-native-isa-notes-101.json SHA-256 8aa174c4d0920acd2a2176a47f4cd38bec4b277acebfc141e69dab3a1e796020.
Reproduce with scripts/build/audit_native_isa_notes.py; this is supplemental
portability evidence, not an alternate-CPU/hardware test pass.
