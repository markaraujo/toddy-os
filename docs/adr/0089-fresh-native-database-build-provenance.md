# ADR-0089: Rebuild native DB test inputs with portable provenance

- Date: 2026-11-07
- Status: Fresh private compilation, C tests and preparation verified
- Scope: H07 build reproducibility; complete standard/production acceptance pending

## Decision and sources

Use the same native test recipe for ordinary and private compilation. Split
berkeley-db-inner.sh into explicit prepare/configure/build stages while retaining
its default complete invocation, compiler flags, maintained patches, configuration
and C tests. The frozen maintained db5.3 5.3.28+dfsg2-12 debian/rules (lines 11,
85 and 109–113) provides the gnu17 and separate test-build pattern; ADR-0032
records the required full standard suite and distinct production profile.
No maintained build script is executed and no test assertion is removed.

scripts/build/db_native_compile.py extracts verified archives into a new private
generation, applies both reviewed Tcl fixture patches, then runs the common
native recipe and test helper. The wrapper privately binds source, evidence and
reviewed build code to their canonical paths. Separate mount/PID/IPC/network
namespaces and temporary tmpfs mounts preserve the active suite and shared
inputs. Compilation uses native tools in the target chroot with -j2 and
CONFIG_SITE=/dev/null. No runtime library is installed.

Each stage has an intent, PID, durable log, actual exit, input digest and completed
marker. A marker requires exit zero; an interrupted supervisor does not allow
resumption over its live compiler. Captured source/code hashes, stage logs, native
package context, 10,207 compiled/source input records and the independently
reconstructed 483 Tcl files form native-build.json. This is compilation evidence,
not a successful standard-suite claim. The preparer from ADR-0088 produces a
separate source view and isolation probe, without launching run_std.

scripts/build/db_native_build_result.py verifies the actual dead producer and
terminal zero, all five stage invocations/exits/logs, exact reviewed code and
frozen archives, compiled source inventory and native context. It also binds the
prepared 10,208-file execution manifest (native inputs plus the standard entry)
to that exact native compilation. Binary digests come from this measured build;
no historical recovery seed or historical helper-binary digest is required.

The native package context is retained as protected bytes matching the digest
checked during the build. Later installed-package changes must not erase this
build-time record. The launcher now captures it before future builds; for this
first experiment it was copied immediately after terminal completion while the
actual status still had exactly the recorded digest. No original receipt changed.
This does not claim an independent rebuild produced byte-identical output or
that the complete release can already rebuild successfully.

Alternatives rejected: reusing only the old recovery seed leaves fresh provenance
unverified; replacing compilation with an input-manifest assertion cannot prove
tools ran; duplicating production configuration risks divergence; running another
hours-long full standard suite here duplicates the still-active corrected run.
Keep the existing full-run obligation and develop its portable integration next.

## Actual target evidence

Fresh generation: /mnt/lfs/sources/recovery/db-native-m3pjqwd2.
Actual driver 4055451 is terminal; source, prepare, configure, build and helper
all exited zero. The native C suite passed. The installed package database stayed
unchanged. Preparation at /mnt/lfs/sources/recovery/db-standard-6gav6kkh passed
its actual private namespace/tmpfs probe. No second run_std was started.

| Evidence | SHA-256 |
| --- | --- |
| Collected terminal report | dc688df3c81ebc7fb555a237651e62fa27b73930e063866a24f2663a9069efce |
| Final native provenance verification | 3eb0c0582108fd2b5f2c50fa9b20de84370c11d6d6c5f9435e026b273f1f4219 |
| Native build receipt | 79bad3e947ece611149dac738c6cf0e0bca3addccbc7e92453923ad04ed416f5 |
| Native result | 9e759b5fbbfac9a65efdf0c1831ec47e6727a569baae45b341067b2080672651 |
| Build inputs | e1834993fc479c9481101b457886b2739b8a9b637c1148ae2d6d6846b8241723 |
| Prepared standard inputs | 45ada2b9916c412d4cf436dea41851082ec6849d5534b2eb1856e0586214d524 |
| Native C-suite log | 51763da1955dcca28f53b8bc863cec7f834179ddd994beda4b55f1cc4ab025d2 |
| Native build log | 5203d10633374ef48527d9c79377179d78e5909ec48f92efec46a4a92c2836ec |
| Captured native package context | 96ce580273ad5ce7f97557905f2be3ae918ee8e6da29ef7167788720b99c6f4e |

Native verification refused an outside generation, the existing standard suite
as compilation provenance, and an altered private reviewed recipe. Concurrent
start/resume were refused while the actual compiler driver was live; resuming
the terminal complete build was also refused. Raw live-refusal reports:
679f70c30d44f0e9154f0a6c66e6bfc2a71c1e7648d4bd53b1cd2cf324673c25
and 28260dba6012fb4883a722614fe873b74eabc0de857be7f7a99aa90acfed3ad8.
Complete-resume refusal:
f70b37614301861f09f20b4ecb203d5ee7db3fc9082fe4e17c10a6cb022d7c93.
Context capture report:
c2170d18abcbed6c0ca698b4be983d031725e0b0e3a2cd78da5a44c34b154551.

The host initially retained remote refusal stderr in its raw file but omitted
it from terminal output. The observation assertion exposed that reporting defect;
the launcher now displays both streams, and both live refusals were verified.
The actual build was neither restarted nor changed to fix output presentation.

## Remaining boundary

The normal fresh recipe still invokes its old plain-chroot standard command.
Integrate private full dispatch, generic complete-result/coverage qualification
and production handoff before calling fresh reconstruction complete. Existing
recovery-result verifiers remain pinned to their actual measured run; do not
replace their native seed with this receipt or accept a partial test result.
H07 stays 124/126 and APT remains gated on accepted database production checks.

## Comparison with the still-running native input profile

A separate read-only comparison found all 460 historical native checkpoint
entries identical to the fresh build. Of 10,207 copied input paths, only four
static archive paths differ: build-test/.libs/libdb-5.3.a,
build-test/.libs/libdb_tcl-5.3.a and their build-test/libdb.a/libdb_tcl.a aliases.
The shared runtime library, test helper, db_config.h and include.tcl have identical
hashes to the running input manifest. Native ar then compared both real archives:
252 and 266 members respectively, identical names/order and zero differing member
payloads. Archive container bytes still differ; no whole-build byte-identity
claim or blanket normalization follows from this comparison.

Input comparison report:
c4411f0e43e571fcdf331072fbc84ca41ce3f5cb3ef2eda1c7ffb0954fea0233.
Actual native archive-member comparison:
343ea2b04fbf79018ab9bc75fbedcbcaef4f3c00792bc39ff68e90d5d62ef4c2.
The running manifest/source and all raw results remain unchanged. This narrows
the reconstruction difference; it does not accept the running full standard
suite or authorize substituting this fresh manifest for its measured inputs.
