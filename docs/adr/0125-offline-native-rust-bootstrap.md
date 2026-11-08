# ADR-0125: Offline native Rust bootstrap in the qualified build namespace

- Date: 2026-11-08
- Status: Accepted preparation/build contract; native execution pending

Use frozen BLFS13.1 Rust1.97.1 source, completed patched LLVM22.1.8 and the three
official1.96.0 seed archives authenticated by Rust's original src/stage0 metadata.
Keep the source and seed trees separate inside one immutable declared input.
The original seed installers use a private /build/bootstrap DESTDIR with /usr
prefix and ldconfig disabled. Their default bindir/libdir/sysconfdir include that
DESTDIR; do not override those defaults with writable system paths. Run only as
UID101/caps0 in the existing network/IPC/PID/mount namespace. Seeds never replace
the installed product compiler.

The authenticated bootstrap.py supports external rustc/cargo/rustdoc paths,
external config/build-dir, vendoring and locked dependencies. Preserve the source
read-only; place outputs and Cargo home under /build. Use source-vendored crates
offline, no CI compiler/LLVM downloads. Prefer the existing SQLite/OpenSSL and
system libssh2 when present; otherwise use the libssh2 already bundled in the
frozen Rust source, as the book permits. No foundation version change.

Build stage2 with four jobs, thin LTO, one codegen unit, the book's selected
cargo/clippy/rustdoc/rustfmt/src tools and docs disabled. Install prefix is /usr
for the build SDK, so no undeclared /opt dependency mount or global PATH hook is
needed. Keep the default GNU linker by the source-supported target override off;
do not introduce LLD, NVPTX bitcode linker or duplicated LLVM tools. The source's
bootstrap.example.toml documents these controls for1.97.1. Initial seed linking
may use its own authenticated bundled linker only as a build input.

Measure space before preparation and build. Preserve100GiB host/16GiB target
reserves; compiler phase starts with26GiB target free and stages nothing. Verify
actual stage2 version/LLVM and a native Vec/thread program before a successful
compile receipt. Critical Rust/std/compiler/tool checks, staging, native ownership,
licensing/inventory and installed consumers are separate mandatory gates. Do not
accept this preparation, seed execution or a successful build as those tests.

Rust is a build SDK for librsvg/Firefox and stays out of the offline base/live
image unless an explicit real runtime dependency proves otherwise. Preserve valid
native archives and raw evidence; retire qualified scratch only after measured
need and verified archive/state, never uncertain work or historical G1 backings.
