# ADR-0127: Native Rust validation in separate bounded gates

- Date: 2026-11-08
- Status: Accepted validation selection; actual test acceptance pending

Native Rust1.97.1 compiler-only build completed0 with LLVM22.1.8 and a real
Vec/thread program. Preserve that cache. The target has21.36GiB free after build;
the frozen BLFS13.1 full test estimate adds11GiB, conflicting with the16GiB
recovery reserve. Split critical validation instead of starting the full matrix
or accepting compilation as testing.

First run the original core/alloc/std unit and integration tests with x.py test
--tests library/core library/alloc library/std, four threads, native unprivileged
read-only-input isolation and private loopback. The authenticated1.97.1 bootstrap
flags.rs maps --tests to TestTarget::Tests; test.rs passes Cargo --tests and adds
coretests/alloctests for core/alloc. These are actual tests, unlike empty core or
alloc lib targets. No doctest, benchmark, cross-target or full compiler-suite pass
is claimed by this slice. Keep native ignores separate from passed cases, raw
exit/log/summaries, compiler tool hashes and measured post-test space. Existing
output refuses replay; unknown failures block acceptance for bounded diagnosis.

Then select original compiler tests for the native language/FFI/async/ownership
contracts and actual cargo/clippy/rustfmt/rustdoc consumers. Document exact scope
and outcomes before stage/package promotion. Staging/install ownership/legal
inventory and installed consumers remain separate gates. No runtime/compiler
failure may be suppressed by this selection. If space becomes insufficient,
measure and retire only independently verified disposable data; preserve original
reports, archives, recovery state and unchanged qualified binaries.

Sources: frozen BLFS13.1 general/rust.html (hash in sources.lock.json), original
Rust1.97.1 src/bootstrap/src/core/config/flags.rs and
src/bootstrap/src/core/build_steps/test.rs from the authenticated source archive
SHA2560ed06fdaffd4722a7702e0b4eebfafc897ab8f513e8e1b247cdd7e5c6df6ded2.
Native GUI, librsvg/Firefox integration and installed product acceptance remain
pending; Rust is a build SDK, not a required offline desktop application.

## First native outcome and collector correction

The bootstrap completed its35 libtest drivers with6223 passed/0 failed/5 ignored,
plus explicit harness=false pipe-subprocess success. Cargo also executes three
bench targets declared test=true in test mode; these are not performance results.
The outer collector then failed hashing stage2/bin/clippy-driver: original
compile.rs deliberately recreates the temporary sysroot. Retained compiled tools
remain in stage2-tools-bin; no compiler rebuild is required. Preserve wrapper1.

The original bootstrap.py success_word branch proves its native success terminal
message follows normal exit0; unknown/missing/failed/custom outputs are refused
by the recovery parser. Record this as derived qualification, not an independently
saved native exit file or unchanged-tool proof. Four recovery guard tests pass.
Corrected future collector persists input hashes and native exit before optional
postchecks. Already passed std tests are reused. Compiler job3 explicitly saves
its own native exit and hashes the actual rustc before/after.
