# ADR-0224: Private browser build tools preserve upstream WASM decoding isolation

Status: accepted
Date: 2026-11-11
Scope: B02 browser compiler prerequisites, not browser security acceptance

The frozen Firefox153.2.0esr source defaults to WASM-sandboxed decoding libraries.
Its `toolkit/moz.configure` requires a WASI sysroot and its
`build/moz.configure/toolchain.configure` requires Clang19 or newer, including
the WASM compiler. The installed qualified Clang22.1.8 only registers native
X86/AMDGPU targets; neither a WASM backend nor `wasm-ld` is available. The frozen
BLFS page recommends disabling WASM libraries, but we will first qualify the
missing private compiler tools to retain this upstream protection. The Linux
content/process sandbox must also remain enabled and separately verified.

Use the official WASI SDK25.0 Linux x86_64 release as an explicit development
bootstrap tool, isolated from the installed compiler and OS package root. Freeze
the release asset bytes/SHA, exact source tag commit and LLVM/wasi-libc/config
submodule commits in `config/phase2/browser-build-tools.lock.json`. This is an
additional compatible build tool, not an upgrade/replacement of the accepted
foundation. Firefox's older wasi-sdk20 source-fetch entry alone cannot satisfy
its current Clang19 minimum with that SDK's Clang16 compiler.

The official release API does not provide an asset digest. Record HTTPS origin,
asset size and the locally frozen SHA before extraction/execution; do not claim
independent binary/source reproducibility or a signature check. Retain exact
revision license texts, including LLVM/runtime and wasi-libc third-party notices,
for any generated code later incorporated into the browser. The archive itself
contains no license files. No release license/security acceptance follows merely
from downloading it. Private tools are not automatically included in the desktop.

Before using this SDK, qualify safe extraction, native ABI, actual isolated
unprivileged C/C++ WASM compile/link, expected output format and read-only tool
mutation denial. Expose only declared tool directories read-only to the existing
compiler sandbox. Never grant egress, system-root writes or access to credentials.

The other missing compiler tool is NASM3.02, already recommended by the frozen
Firefox page. Freeze its official source through the existing book-source helper;
compile and stage in the qualified namespace with exact assembler/link/execute
and disassembler checks. The official archive contains three0600 files including
Makefile.in. Preserve the original failed build; make only these files0644 with
unchanged contents for UID101 read access. Reconfigure in a new directory; do not
re-extract or claim an upstream test suite where the frozen book declares none.

Sources: frozen BLFS13.1-systemd general/nasm.html and xsoft/firefox.html; the
authenticated Firefox source paths above; [official SDK25 release](https://github.com/WebAssembly/wasi-sdk/releases/tag/wasi-sdk-25).
Exact source/license URLs and hashes are in the build-tool lock. SDK qualification,
browser configure/compiler/install/ABI/security and native UI acceptance remain
pending until their actual results exist.
