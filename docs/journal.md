# Development journal

| Date | Milestone | Action | Verified outcome |
| --- | --- | --- | --- |
| 2026-11-05 | Bootstrap | Captured user requirements, private-repository preference, approved branding and two-phase delivery plan | Planning documents and approved PNG assets created; OS work has not started |
| 2026-11-05 | Bootstrap | Owner declined workstation RAG integration; removed project manifest and instructions | Repository-native context selected in ADR-0002 |
| 2026-11-05 | Pre-start audit | Read-only host/tool snapshot; fixed H01/H02 source-freeze ordering | Hardware resources/KVM present, VM tooling absent; no provisioning or OS build performed |
| 2026-11-05 | Autonomy policy | Owner authorized installation/configuration of project dependencies for autonomous unblocking | PRD, AGENTS, handoff and H01 updated; no installation started |
| 2026-11-05 | Delivery policy | Owner requested one-start autonomous execution and a single public repository with Pages | ADR-0004/0005 recorded; OS build still not started |
| 2026-11-05 | H01 | Started implementation; inventoried host, provisioned isolated KVM guest and installed guest build dependencies | LFS 13.1-systemd host check passed before/after guest restart; offline builder checkpoint retained; no host package/service changes |
| 2026-11-05 | H02 | Downloaded pinned LFS/BLFS books; verified 94 systemd inputs; reviewed current advisory application | All upstream MD5 checks and SHA-256 pins passed; corruption negative tests added; known security remediation explicitly retained for release |
| 2026-11-05 | H03 | Prepared serial-guarded guest target, clean lfs environment, native package prototype and durable runner | Install/update/conflict/recovery and negative-marker tests passed; paired offline checkpoint retained before toolchain work |
| 2026-11-05 | H04 | Started source-verified chapter 5 recipes under lfs with durable driver | Binutils pass 1 recipe/postcheck passed; GCC still running; fixed source-directory transfer mode without installing host software |
| 2026-11-05 | H04 | Completed chapter 5 binutils, GCC, headers, glibc and libstdc++ with per-step postconditions | All five recipe/postcheck exits 0; target-loader C execution and search-path checks passed; full logs/manifests copied and paired offline checkpoint saved |
| 2026-11-05 | H05 | Completed 17 temporary-tool recipes with target-only runtime audit and ownership/PATH checks | All recipe/postcheck exits 0; controlled pre-install gzip interruption had no installed changes and restarted successfully; paired offline checkpoint saved |
| 2026-11-05 | H06 | Completed native chroot, eight temporary packages and /tools cleanup; restored a cold disk pair after controlled change | C/C++ ran natively; post-cleanup C/Python/Perl checks passed before and after actual restoration; verified checkpoint h06-ready retained |
| 2026-11-05 | H07 | Staged and installed first two final native packages in book order; retained source/license/payload metadata | man-pages and iana-etc passed; actual conflicting ownership rejected before install with zero changed paths; critical suites still pending |
| 2026-11-05 | H07 | Validated patched final libc, locales/time zones and compression libraries through PCRE2; saved h07-early-base | 13 native packages passed; libc 6779 PASS/16 XFAIL/583 UNSUPPORTED/one source-documented chroot failure; full raw results retained; native container retest remains required |
| 2026-11-06 | H07 | Corrected detached signal/PTY transport defects; installed M4/Bc/Flex/Tcl and native harness through Pkgconf | 21 native packages; M4 334 PASS, Tcl core 43704 PASS/zero failed with optional database limitations; Binutils build/suite running, H07 incomplete |
| 2026-11-06 | H07 | Accepted full final Binutils against official 13.1 reference, installed generic GMP/MPFR/MPC and saved h07-native-math | 25 native packages; mandatory suites retained, only exact documented profiler failure; 199/198/75 math tests passed; Attr/ACL started |
| 2026-11-06 | H07 provenance | Extended runner/archive metadata to cover inner/supporting script hashes; retained active GCC input sidecar | Regression test detects inner-only recipe change; original running record preserved; no in-progress compiler recipes changed |
| 2026-11-06 | H07 independent verification | Exported verified 31-package native inventory; inspected/froze dpkg 1.22.22 and security-fixed APT 3.0.4 source additions | Archive/source/copyright hashes pass; official DSC checksums match; no target binary packages imported and native package-manager builds remain pending |
| 2026-11-06 | H07 security freeze | Verified Patch signature and pinned Patch/Vim/Expat/util-linux fixes in ADR-0013 while GCC tests run | Four archive hashes verified; selected Expat 2.10.0 adds Nov 2 fixes beyond LFS snapshot; unresolved upstream risk remains visible; final builds pending |
| 2026-11-06 | H07 source authentication | Resolved Xz signing-key retrieval through Debian-maintained upstream key copy and matched official source metadata | gpgv valid for unchanged Xz 5.8.4 archive; explicit key-origin trust basis retained; no global trust changes or unchanged package rebuild |
| 2026-11-06 | H07 final compiler preparation | Added hash-pinned six-suite classifier and staged compiler/runtime ownership split, ADR-0014 | Regression tests reject incomplete/novel results and invalid runtime staging; actual compiler/runtime installation remains gated on the ongoing complete suite |
| 2026-11-06 | H07 dependency evidence | Audited 445 actual native ELFs with target-root symlink resolution; verified unchanged GCC archive signature | Explicit temporary providers and four missing dependency pairs retained for repair; no false closed-graph claim; GNU signature valid |
| 2026-11-06 | H07 critical compiler | Completed and classified all six final GCC suites; copied complete merged/parallel reports and runner evidence | 511240 PASS, 72 reference-known FAIL/two reference-known XPASS, zero unexplained; installation still pending; cold tested-state checkpoint being saved |
| 2026-11-06 | H07 native compiler | Verified h07-gcc-tested cold pair, installed GCC/runtime and Ncurses with explicit zero-mutation packaging recoveries | 34 native packages; C/threaded C++ and terminal tests passed; original failures retained; Sed onward running, H07 incomplete |
| 2026-11-06 | H07 base continuation | Installed/tested Sed and Psmisc; fixed stderr version capture via unchanged-package audit | 36 native packages; original failed postcheck retained; Gettext onward resumed; six next book recipes prepared but not claimed validated |
| 2026-11-06 | H07 Gettext and next recipes | Accepted full Gettext and native translation; prepared frozen recipes through Meson and generic Libffi ADR-0015 | 37 native packages; Bison suite running; prepared recipes await actual target acceptance |
| 2026-11-06 | H07 Bash diagnosis | Bison/Grep/test locales passed; rejected initial Bash output, isolated leaked FD 4 and pinned official reference in ADR-0016 | 40 native packages; full corrected PTY suite running, no Bash installation yet; 36 local regression checks pass |
| 2026-11-06 | H07 Bash acceptance | Completed corrected full 86-group PTY suite and strict known-result classification, then installed Bash and audited ordinary printf/signal semantics | 41 native packages; zero novel differences, seven source-qualified diff lines retained; native-tools driver running |
| 2026-11-06 | H07 tools and source support | Accepted Libtool through Perl, corrected Gperf caller fixture, saved verified 47-package recovery cache and froze CMake support in ADR-0017 | 48 native packages; Perl 1392301 tests successful; Autoconf onward running; supplemental builds remain pending |
| 2026-11-06 | H07 crypto/FFI and patch recovery | Accepted base through mpdecimal; verified/froze Python context adaptation with no removed SSL tests; saved 55-package recovery cache | 55 native packages; OpenSSL 4413 tests and Libffi 2564 passes; native Python build remains pending; preparing cold checkpoint |
| 2026-11-06 | H07 verified checkpoint/resume | Saved h07-native-crypto with both image/hash checks, restarted/remounted and started Python recovery with source-byte/patch verification | Native Python build/tests running; success-gated remaining drivers queued; no new restore or completed release claim |
| 2026-11-06 | H07 Python/utilities | Repeated full Python suite after verified build DNS repair; accepted offline Python tooling, Kmod, Coreutils, Diffutils and fixed Findutils regex selection | 65 native packages; Python Result SUCCESS with 48840 reported/2159 skipped; Groff PATH recovery running; all release gates remain pending |
| 2026-11-06 | H07 input integrity | Added shared build lock, verified staged transfer and interrupted-input dispatch guard | 39 local tests pass; actual guest busy-lock and incomplete-input refusal probes pass; no active recipe overwritten |
| 2026-11-06 | H07 utility acceptance | Accepted Groff full PATH retry, GRUB dual core-image generation and utilities through Patch; refreshed two Kbd patch context lines with identical-output proof | 73 accepted native packages; actual boots remain pending; Tar complete suite classified one display mismatch with exact capability-byte probe passed |
| 2026-11-06 | H07 final base preparation | Prepared service/filesystem and TLS/CMake dependency recipes, froze dated public CA data, scoped documentation-link checks to Git-visible files | No prepared package claimed accepted; checker still validates tracked and new docs, excludes ignored external source trees |
| 2026-11-06 | H07 services/TLS acceptance | Accepted Tar ACL/capability, final services and E2fsprogs real ext4 remount/persistence; verified native CA/Nghttp2/Curl positive and negative TLS | 86 accepted packages; Systemd 1828 OK/33 SKIP/one qualified chroot namespace failure remains native-retest obligation; 50 local tests pass |
| 2026-11-06 | H07 recovery and signing freeze | Saved verified 86-package cache/raw reports, stopped orchestration after completed Curl, verified six signing archives with both official fingerprints | Cold pair saving; supplemental source builds pending; Vim gated on frozen plugin inputs; no ISO or release completion claim |
| 2026-11-06 | H07 cold checkpoint | Verified h07-native-services paired images and copied hashes, save exit 0 | 86-package boundary recoverable by paired restore; this new pair not yet restored; restarting builder for supplemental source builds |
| 2026-11-06 | H07 native build support | Accepted complete Libuv group-ownership retry, Libarchive, CMake 674/674 and Libmd native checks | 90 native packages; source-verified GNU Time/full XXHash recovery running; no native dpkg/APT yet |
| 2026-11-06 | H07 reproducible test inputs | Froze four Vim plugin version IDs/hashes and prepared fail-closed live download guard with unchanged tests; all 19 DB patches pass strict source-only preflight | 55 local regression tests pass; native Vim preflight/full suite and DB compile/tests remain pending |
| 2026-11-06 | H07 signing/editor acceptance | Accepted Time/XXHash, GoogleTest, signing chain and unchanged Vim PTY suite; retained verified 100-package cache | Vim 8014 executed/200 skipped/zero failed; native signing/tamper tests passed; Dpkg FIFO extraction narrowly corrected and full build retry started |
| 2026-11-06 | H07 native package manager | Native Dpkg full suite and isolated operations passed; corrected DB test/static-object prerequisites; complete Tcl suite running | 101 accepted packages; 2551-ELF/ownership audits expose closure work; native backend and APT recipes prepared, 61 local tests pass |
| 2026-11-06 | H07 ownership review | Verified 58815 payload entries and exact privileged helper identities; prepared root ownership correction for four CMake license entries | Only shared generated Info hash differs; 67 local checks pass; unchanged BDB Tcl suite running, no new package acceptance claimed |
| 2026-11-06 | H07 native package safety | Unified private archive workspace validation across build/install and metadata extraction; checked default coverage report source dependencies | 73 local tests pass; Berkeley DB full Tcl suite still running with no acceptance claimed |
| 2026-11-06 | H07 runtime boundary review | Native Autotools shared-library flow passed; mapped nine Expat consumers and tested DBus config rejection as unprivileged user | No new package accepted; 150 source inputs/880 legal candidates inventoried; complete XML exposure audit remains pending in ADR-0041 |
| 2026-11-06 | H08 preparation during H07 tests | Prepared gated source-derived config, exact bootstrap backups and mutable timezone/DNS policy | 81 local tests and staging checks pass; H08 gate refuses current state; no H08 target installation or story completion |
| 2026-11-06 | H07 DB fixture diagnosis | Reproduced test139-to-test142 environment flag contamination with same native library; unchanged test142 passes after prior cleanup | Known-failed full attempt stopped via verified PGID; recipe -15, zero installed changes; mandatory correction/full rerun pending, independent support packages next |
| 2026-11-06 | H07 independent support acceptance | Accepted 16 CPAN suites/provider checks with native Dpkg; corrected shared Perl diary ownership through Tagset metadata | 117 accepted packages; all seven Triehash upstream tests passed but filename-based CLI postcheck recovery still pending; BDB focused correction exit 0, full rerun required |
| 2026-11-06 | H07 native support recovery | Repeated all Triehash upstream tests and corrected generated-C postcheck; accepted native Which | 119 accepted packages; Libseccomp full tests running, Tcsh next; independent ownership driver prepared, BDB full rerun mandatory |
| 2026-11-06 | H07 native support complete | Accepted Libseccomp full standard tests and native syscall filter, Tcsh full suite and shell behavior | 121 accepted packages; independent ACL/ownership next; cached DB test-file verification and complete standard rerun still mandatory |
| 2026-11-06 | H07 independent ownership | Full ACL cp retest and Linux API/filesystem layout accepted; build-support check exposed Glibc patch-49 cache mismatch | 123 accepted packages; versioned native cache correction prepared in ADR-0044, acceptance pending; no G1 or ISO claim |
| 2026-11-06 | H07 native configuration correction accepted | Versioned stale bootstrap-cache removal passed real configure and both spawned-child directory checks | 124 accepted packages; preserving verified cache/cold pair before full corrected DB suite; APT/final closure and H07 remain pending |
| 2026-11-06 | H07 native-support checkpoint | Saved verified paired cold images and 124-package archive cache, restarted builder | Save exit 0 with both image/hash checks; no restore claim; complete corrected BDB suite is next |
| 2026-11-06 | H07 corrected DB standard rerun | Verified 460 build files/483 Tcl inputs, repeated C tests and three focused regressions, started complete suite | Full result unfinished; independent native Perl audit found 330 staging entries and validated private canonical fixtures; versioned correction prepared only |
| 2026-11-06 | H09 preparation during H07 tests | Prepared gated generic kernel recipe, checked 137 symbols against frozen source and refused premature gate | 90 local checks pass; no kernel target execution/boot, H09 remains not_started; full BDB suite still active |
| 2026-11-06 | H10/H11 source preparation | Native bsdcpio newc metadata/gzip experiment passed; verified and froze four image-tool sources | 155 source inputs; no guest input sync, native tool build, image or boot acceptance; H07 DB standard suite still running |
| 2026-11-06 | H10 metadata experiment | Identified Squashfs ACL namespace limitation; native numeric/escaped ACL sidecar and effective UID-101 access roundtrip passed with physical restore | Private fixture only, no package/image mutation or boot claim; real overlay/installer integration remains pending in ADR-0048 |
| 2026-11-06 | H07 progress visibility | Added separate active-story facts/running/remaining panel and explained accepted-only 38% versus H07 24 pending points | 91 checks pass; exported dashboard inspected in browser; no partial credit or changed acceptance, DB suite continues |
| 2026-11-06 | H11 QA partition preparation | Verified 15 public upstream Python key fixtures; staged 5395 QA files with 3943 runtime entries unchanged from own archive | 95 local checks pass; no installed package/ownership or image change; actual transfer/exclusion still pending, H07 DB suite active |

2026-11-06: Prepared LFS 13.1 direct-root UUID/PARTUUID GRUB renderer; actual native GRUB 2.14 syntax check passed in private temporary staging. No boot configuration or disk changed; H09 installation/boot remain pending (ADR-0046).

2026-11-06: Prepared gated native boot-config packaging without dispatch. Native grub-fstest followed its exact configuration symlink in a private regular-file ext4 image; bytes and syntax passed. No block device changes or actual boot claimed (ADR-0046).

2026-11-06: Armed a session-local success-gated H07 continuation: complete BDB result/postchecks, quiescent clean committed input sync, then native final-base driver. Durable supervisor state/logs are outside Git; failure stops for diagnosis and no milestone is automatically accepted.

2026-11-06: Fixed prepared Python metadata generation idempotency after the actual interpreter audit exposed later bash/coreutils edges. Actual native Python/SSL private alias retry passed; 97 checks pass. No installed upgrade or H07 acceptance claimed (ADR-0036).

2026-11-06: Revalidated the live BDB memory-pool workers and supervisor. Prepared final-base driver exit capture before prerequisite refusal; shell syntax and 97 checks pass. No active build inputs changed.

2026-11-06: Prepared gated dual-platform GRUB installation, target/partition checks, before-sector recovery copies and boot artifact verification. Actual gate refused premature execution; syntax and 97 checks pass. No disk writes or boot acceptance; BDB full suite remains active (ADR-0046).

2026-11-06: Frozen signed GNU Mtools 4.0.50 after verifying the GRUB EFI image dependency, detached signature and safe archive paths. Future native FAT roundtrip/ISO boot remain pending; no active guest inputs changed (ADR-0050).

2026-11-06: Prepared gated native Mtools build and exact GRUB FAT-image acceptance checks. Actual premature H11 gate refusal verified; syntax and 97 local checks pass. No Mtools install/FAT runtime acceptance or active input sync performed (ADR-0050).

2026-11-06: Prepared gated Squashfs build and three-compressor native metadata/ACL roundtrip checks from frozen sources. H10 premature gate refusal verified; syntax and 97 checks pass. No tool build, image acceptance or active input sync performed (ADR-0047/0048).

2026-11-06 20:05 UTC: Revalidated the running H07 database suite and automatic continuation supervisor; observed progression into Dead006 and refreshed the published active-work snapshot. Accepted count remains 124/126, foundation credit 38%; full result and final closure remain pending.

2026-11-06: Native private preflight using frozen APT discovery modules found all four selected optional libraries. The prepared APT recipe now refuses missing Seccomp/Systemd/Udev/Zstd definitions and preserves its generated configuration. No installed package or active BDB input changed; full APT acceptance remains pending (ADR-0034).

2026-11-06: Prepared gated source-built libburn/libisofs/libisoburn recipes from frozen BLFS and native API/ISO metadata/corruption checks. Reviewed command/exit semantics against frozen Xorriso source documentation. No target dispatch, new package acceptance or bootable ISO claim; the complete H07 database suite remains active.

2026-11-06: Prepared firmware-only native boot probe with virtual-disk/kernel guards. Actual native Systemd generator/unit verification and wrong-kernel refusal passed; added source-verified DMI sysfs support to the gated kernel fragment. Existing BIOS/UEFI firmware inventoried. No kernel build, firmware import or native boot claimed (ADR-0051); BDB full suite advanced into Dead008.

2026-11-06: Prepared guarded H09 checkpoint-overlay boot executor. Real paused BIOS/UEFI QEMU setup, read-only backing preservation, timeout cleanup, wrong-identity refusal and overlapping-run refusal passed; actual main executor refused premature gates. Four safety tests added. Native Toddy boot remains pending; BDB standard suite advanced to Dead011.

2026-11-06: Prepared a gated native early-userspace runtime and verified its
twenty files from eight accepted packages in a private real chroot. Program
execution, content hashing and fixed device nodes passed; no credentials or
installed changes. Three path/preservation tests pass. This is not a booted
initramfs or H10 acceptance (ADR-0052). Complete BDB regression remains active,
advancing through secondary-index tests at 20:52 UTC.

2026-11-06: Corrected prepared APT postcheck recovery to retain failed private
repositories while terminating their child processes and preserving failure
status. Actual native shell cleanup checks passed exit 0/removal and exit 37/
retention; this does not claim APT acceptance. BDB complete standard suite is
still live, now exercising transaction recovery after secondary-index tests.

2026-11-06: Actual private builder-kernel overlay experiment exposed hardlink
splitting during ACL copy-up with index=off. Repeated with index=on: effective
option, inode identity, real write propagation, permissions, unchanged read-only
lower and volatile upper disposal passed. Recorded the required live profile
and reusable experiment in ADR-0048; actual Squashfs/native-kernel integration
remains pending. H07 full DB recovery tests continue; no milestone credit added.

2026-11-06: Native private Linux configuration resolved all 139 requested
settings. The subsequent release query exposed stale auto.conf after the
fragment merge. Source-backed make prepare correction passed with
7.1.8-toddy and unchanged resolved config hash. Prepared H09 recipe corrected;
no kernel image/install/boot produced, and BDB full recovery suite stays active.

2026-11-06: Actual native minimal runtime passed a PID-1 switch_root experiment
between distinct private tmpfs roots, retaining dev/proc/sys/run mounts and
runtime state. Corrected an initial test-only env dependency and retained its
failure log. Builder kernel only; no live/ISO boot or H10 acceptance claimed.
Reusable experiment and recovery recorded in ADR-0052; full BDB suite advances
through Recd003 recovery cases without a final result yet.

2026-11-06: Prepared live-media identity/root-hash verification using only the
native minimal runtime. Ten real native file cases passed, covering changed
bytes, wrong/malformed metadata, absent/redirected payload and non-evaluated
command-like text. Documented remaining discovery/real-image/boot integration
in ADR-0053; H07 database recovery tests continue and no H10 credit is claimed.

2026-11-06: Prepared the real live /init sequence: constrained ISO discovery,
embedded identity/hash checks, read-only Squashfs, indexed volatile overlay,
ACL restore and native Systemd switch. Native non-PID-1 refusal passed before
mounts. Real media discovery/rescue/boot remain untested and gated; the complete
H07 BDB suite is still progressing through recovery cases.

2026-11-06: Verified actual native set-ID execution with the planned nosuid
upper storage: overlay execution preserves the reviewed helper semantics before
and after copy-up, while direct upper execution remains unprivileged. Repeated
ACL/hardlink/volatility checks passed; older evidence generations preserved.
Builder-kernel fixture only, with real live-root acceptance still pending.

2026-11-06: Investigated possible hidden BDB block/infinite loop at the owner's
request. Two live snapshots proved checkpoint 59-to-104 progress in the same
variant. Verified source shows finite inclusive iteration and timed waits;
prior variant timing matches. No current resource exhaustion or retry loop
found. Preserved evidence and continued the original full standard suite.

2026-11-06: Published a source-backed H07 remaining-volume breakdown after the
owner requested concrete scale. Recorded actual pending markers and separated
package count from the database's nested test matrix and final package audits.
No tests were shortened and no acceptance percentage changed.


2026-11-06 21:46 UTC — Prepared the gated native minimal-initramfs archive
component and validated two fresh private native assemblies (ADR-0054). Both
44-entry archives were identical, and real native extraction preserved content,
modes, root ownership, links and devices. Extracted /init refused non-PID-1
execution before mounts; integrity-helper loading and embedded metadata readback
passed. Modified executable/truncation/existing-stage cases were rejected.
Full raw manifest/provenance retained outside Git; successful fixtures removed.
Actual kernel unpacking, live-root/ISO construction and boot remain pending.
The original complete Berkeley DB standard suite continues, now in partition
Test014 after Recd024; no source sync or installed mutation occurred.


2026-11-06 21:54 UTC — Verified the frozen DB numbered dispatch list directly:
Test001 through Test142 with 135 entries (seven upstream numbering gaps).
Corrected the earlier conversational statement that it ended at Test135.
Test044 has three timed load/crash/recovery cycles; current first cycle is
525 seconds with five CPU-active native workers. Published the precise
sequence and source-backed wait context without assigning fractional acceptance
or shortening the suite. Original driver/supervisor remain active.


2026-11-06 21:58 UTC — Added a read-only private-key-marker audit that reports
paths/hashes without key bodies, plus a reproducible native own-archive probe.
Actual CPython extraction/QA separation preserved all 15 public regression-key
fixtures outside the prepared runtime, with exact file/byte conservation.
Recorded evidence and scope limitations in ADR-0049; no installed package or
active recipe changed. Three local regressions cover marker boundaries,
non-disclosure and link handling. Native QA ownership transfer and final image
audits remain pending. DB Test044 cycle 1 continues its programmed load with
five CPU-active workers; original runner and supervisor remain live.


2026-11-06 22:01 UTC — Observed Test044's timed first-cycle crash, subsequent
recovery/file verification and transition into cycle 2 (446 seconds). Updated
the public activity snapshot without assigning completion credit. Both native
runner and supervisor remain live; the full suite/result is still required.


2026-11-06 22:07 UTC — Verified real native Dpkg ownership transfer for CPython
QA in separate private package roots. Wrong-order transfer fails without
overwriting original QA bytes; correct core-then-QA order preserves all 5,395
file payloads, modes, owners and mtimes. Predecessor/new archives remain
available at the intermediate recovery boundary. Compression is limited to
two threads. No installed state changed; both fixture package states are
unpacked and do not claim configured/runtime acceptance. Recorded the remaining
production archive-preparation/transfer requirement in ADR-0049. DB's original
full standard suite continues in Test044's second timed cycle.


2026-11-06 22:10 UTC — Observed the current Test044 invocation enter its third
cycle after the second timed crash/recovery. Published the actual 370-second
load interval and retained the distinction between one invocation and remaining
method/partition variants. Full DB recipe and H07 acceptance remain pending.


2026-11-06 22:16 UTC — Added a narrow H11-only archive preparation mode for
complete unchanged Python QA, retaining ordinary package ownership refusal
and forbidding installation through the preparation flag. Actual native
preflight validated all 5,395 files and rejected install mode/altered staging;
restored staging passed. No installed/cache mutation or active recipe sync.
The first Test044 range-partition invocation finished with three recovery
cycles plus ten each database/dump-load/salvage successes and no FAIL marker.
Original suite advanced to callback partition, first cycle 366 seconds.


2026-11-06 continuation — Reproduced and corrected a Python namespace collision
in the prepared QA handoff: a regular external h11 package could shadow the
phase directory. Explicit project-file loading now passes a fresh-interpreter
regression and repeated native 5,395-file preflight. Physical private source
mirrors exercise the actual import behavior; no installed/cache or active DB
input changes. Original and corrected evidence retained in ADR-0049.


2026-11-06 22:34 UTC — Corrected the prepared Python QA direct dependencies
after native executable-provider inspection. Repeated native preflight passed.
An actual SIGKILL during replacement unpack in a third private Dpkg root left
the old version half-installed; replaying preserved core then QA recovered all
5,395 files without changing installed target state. Added a pure resumable
next-action policy and replayed actual states with native Python. Production
controller and configured runtime acceptance remain pending. DB callback
Test044 has advanced into cycle 3 after two observed load/crash/recovery cycles;
original driver/runner remain live. No active inputs synchronized.

2026-11-06 22:38 UTC — Added the gated archive-only Python QA preparation recipe
and complete core/QA pair validator. The expanded private native preflight built
and re-extracted both real archives with an explicit two-thread compression
budget: 5,395 QA files and 3,943 runtime files/links match the original partition
exactly. Deliberate retained-runtime drift is rejected along with the earlier
negative cases. Installed package state/cache are unchanged. The full gated
production recipe and transaction controller remain unexecuted/pending; no H11
credit or active-input synchronization. DB Test044 callback cycle 3 continues
its programmed load, with the original driver and runner live at 22:38 UTC.

2026-11-06 22:48 UTC — Implemented the gated Python QA transfer entry and durable
native executor. The private configured probe installs 22 own dependency
packages, interrupts after real core configuration before exit capture, refuses
an unrecorded continuation, resumes QA, and passes exact payload/ownership,
Dpkg audit and Python/SSL/SQLite checks. An idempotent repeat performs no native
package actions. Retained full dependency/action logs, journal and evidence
hashes in ADR-0049. The separate direct SIGKILL probe covers half-install state;
not every crash point is claimed tested. Gated installed-target execution and
final image exclusion remain pending. The original DB suite passed both
observed partition Test044 cases and reached Test081 by 22:45 UTC; H07 remains
124/126 and incomplete. Active build inputs were not synchronized.


2026-11-06 22:56 UTC — Added fresh live-account assembly data/component from the
exact frozen LFS 7.6 identity blocks. Native Systemd intentionally lacks sysusers
under the book configuration, so no new dependency or frozen-option change was
introduced. Actual Shadow pwck/grpck validate 14 locked users/34 groups in a
private root; existing/redirected input and root-home state are preserved and
rejected. Corrected a probe-only expected group count and retained its failure.
Image/boot/login integration remains pending. The original DB suite reached
both partition Test142 variants, then Recd001 hash recovery; current snapshot
and active runner IDs are retained outside Git and published without acceptance
credit. No active build input or installed account was changed.


2026-11-06 23:04 UTC — Added an explicit live-root copy component using native GNU
Tar with a NUL inventory, no recursive descent and verified complete metadata.
The actual native fixture preserves hardlinks, ACLs, capability/user xattrs,
special mode/numeric owners, nanosecond mtime and sparse storage. It excludes
unselected siblings/subtrees and rejects traversal, redirected parents, special
nodes, filesystem crossings and an existing destination. Full image selection
and integration remain pending (ADR-0056). The original DB suite progressed to
Recd003 after Recd001/Recd002; active driver/runner remain live. No installed
package or running build input changed.


2026-11-06 23:17 UTC — Derived an actual 124-package candidate image namespace:
63,132 paths, including 60,397 files/links. Strict full preflight correctly
refused the existing Glibc-owned shared Info index; an independent full audit
found only that known final H07 metadata obligation. No mismatch was waived or
installed state rewritten. The prepared closure already removes that ownership
and regenerates the index after DB/APT. Actual inventory also exposed the
legitimate DBus machine-id symlink; corrected the fresh-account integration to
retain only its canonical root-owned alias while generating an empty identity.
Native Shadow and five negative cases pass. Full image integration and H07
acceptance remain pending. The active DB suite continues its recovery cases.

2026-11-06 23:33 UTC — Implemented a fresh-stage live-console profile for tty1
and ttyS0 only, guarded by the explicit live kernel parameter and a volatile
marker created after verified root setup. Native Systemd unit verification and
both actual agetty/Shadow/Bash terminal commands pass; ordinary locked-password
login and unprivileged preauthentication are refused. Private namespaces/devpts
leave installed accounts and package state unchanged. The updated /init also
passes native archive/extraction and repeatability checks. ADR-0058 records
source behavior, root-console policy, installer removal requirements and the
remaining real boot tests. No H10/G1 credit is claimed. Berkeley DB advanced
through Hash Test044's first 512-second workload and recovery to cycle 2 at
23:32:24, with its original driver/runner still live and no partial FAIL lines.

2026-11-06 23:41 UTC — Prepared native package-database image state: 261 files,
7,525,809 bytes, 124 package identities, identical native queries and clean audit.
Validated both a fresh destination and actual Dpkg-owned empty directory layout.
Actual Dpkg writer exclusion and nine refusal/preservation cases passed in private
fixtures. Investigated the first assertion failure: Dpkg truncates its empty lock
files before attempting locks, changing only their mtimes on a refused writer.
Corrected the snapshot without excluding DB data checks; recorded ADR-0059 and
recovery. Installed package state and active build inputs remain unchanged.
Berkeley DB Hash Test044 completed its second crash/recovery and began cycle 3
at 23:41:36 for 450 seconds. Driver/runner remain live; full suite still pending.

2026-11-06 23:50 UTC — Native offline service integration found and corrected
two future H08 failures: DBus's already vendor-activated socket reports static,
and networkd's Also= re-enables wait-online after preset-all despite the Toddy
disable rule. Shared native configuration/check code now verifies 329 own unit
paths, preserves DBus vendor activation and uses an explicit reversible mask
only for network waiting. Native configure/repeat/preset checks, six negative
configuration cases and five mask-audit boundaries pass. Installed services/
configuration and active H07 inputs remain untouched; real boot/networking is
pending. ADR-0060 records the source-backed book deviation and recovery.
Berkeley DB Hash callback Test044 completed three crashes/recoveries and ten
file/salvage verifications each, advancing to Test081 in the partition block.
Original driver/runner are live; the complete standard-suite result is pending.

2026-11-06 23:55 UTC — Berkeley DB full standard run moved from partition tests
to compression (block 19), with Test014 observed. Original driver/runner remain
live and the partial log has no FAIL lines. Published this major group transition
without claiming complete-suite success or changing H07's 124-package boundary.

2026-11-07 00:04 UTC — Prepared fresh live filesystem/time/resolver configuration
and verified native Findmnt, UTC Date and Systemd fstab generation in a private
root. Eleven refusal cases preserve inputs; installed configuration/Dpkg state
remain unchanged. Recorded explicit conffile transformation and recovery in
ADR-0061. Actual base installation and live boot/DNS are still pending.
Berkeley DB remains in compression Test044, cycle 1 (554 seconds), started at
23:57:59 UTC; original driver and runner are live. No package acceptance changed.

2026-11-07 00:09 UTC — Fresh native Info-index generation passed with 130
source-owned document inputs and 71 primary manuals. Two generations yield
identical bytes; native readers locate/read four manuals and navigate two actual
menu entries. Eight negative cases preserve inputs. Classified the sole
no-menu-entry warning against frozen Texinfo behavior and actual gawknotes
content. Installed index/package state and active build inputs are unchanged.
Recorded ADR-0062; H07 shared-index metadata closure remains mandatory.
Berkeley DB compression Test044 completed cycle 1 crash/recovery and started
cycle 2 at 00:07:49 UTC for 442 seconds. Original driver/runner remain live.

2026-11-07 UTC (2026-11-06 America/Sao_Paulo) — Owner amended the execution
boundary: continue through H13, deliver the foundation for testing, and wait for
explicit approval before B01 onward. Recorded ADR-0063 and updated AGENTS, PRD,
development handoff and published scope. Foundation implementation remains
active; this is a future review pause, not a present stop or a completed release.

2026-11-07 00:15 UTC — Native image loader-cache component passed: two fresh
roots generate the same five-entry cache, Bash's native loader trace uses it,
and twelve invalid-input cases are refused. Corrected the initial full-system
/lib64 layout assumption from actual frozen LFS/package evidence (ADR-0064).
Native package links and installed caches/status are unchanged. This is a real
component subset, not full-root/boot acceptance. Berkeley DB remains active in
compression Test044; the supervisor still waits for its complete terminal result.

2026-11-07 00:22 UTC — Confirmed Berkeley DB's actual consumer in frozen APT is
apt-ftparchive's repository metadata cache and recorded the source chain. Image
integration review found the missing _apt account; added the explicit fresh
UID/GID 100 identity without inheriting builder accounts. Native Shadow/NSS,
privilege-drop/access checks and live-console regression pass (ADR-0065).
Prepared APT postchecks now reject root-fallback diagnostics; actual APT
acquisition remains pending. Active build inputs and installed accounts are
unchanged. Berkeley DB compression Test044 completed and execution advanced
to Test076; the complete standard suite is still running.

2026-11-07 00:27 UTC — Implemented native physical/numeric ACL sidecar capture
for fresh images. Corrected an initial filename-decoder type error, then verified
native capture/strip/restore with default ACLs, escaped names, hardlinks, special
mode and UID 101 access boundaries. Existing/partial output, special nodes,
redirected parents, a real tmpfs boundary and invalid streams are refused.
Extended ADR-0048 and recovery; actual Squashfs/native boot remain pending.
Berkeley DB advanced beyond compression into automated repmgr (block 20);
original driver/runner remain live and the partial log has zero FAIL lines.


2026-11-07 00:37 UTC — Corrected an image integration defect: owned mutable
directories would otherwise retain builder cache ownership/ACLs. Recreate them
from package metadata with explicit native APT UID 100/root-group overrides
(ADR-0066). Native identity/access, inherited-ACL isolation and seven refusal
cases passed. The full payload preflight still correctly rejects unfinished
H07 Info metadata. Berkeley DB remains live in automated repmgr election tests,
zero partial FAIL lines; supervisor remains alive and waiting. No package or
story acceptance was advanced.


2026-11-07 00:42 UTC — Reproduced and corrected nested POSIX lock release before
image composition: real private Dpkg could acquire the database after inner
context exit. Shared descriptor lifetime now preserves exclusion until the last
reader exits, including inner failure. Native full-database staging under an
outer transaction preserves both source locks; all existing database-copy and
refusal checks pass. Evidence/recovery extend ADR-0059. Berkeley DB remains
active in automated replication-manager initialization (block 20); H07 acceptance
and the complete image remain pending.


2026-11-07 00:50 UTC — Berkeley DB advanced beyond automated repmgr, revealing
two failures. Reproduced repmgr007's asynchronous diagnostic race with unchanged
native binaries; the expected message appeared 200 ms later. A bounded-read
correction preserves the assertion and passed three complete repetitions.
Confirmed the separate db_repsite failure is missing upstream test source, not
just a disabled C++ build; an isolated C++ attempt fails on the absent source.
Retained both failures, prepared the fixture patch, and started the complete
other_repmgr group privately. No active inputs were synchronized, no group was
removed, and no BDB/APT acceptance advanced. See ADR-0067.


2026-11-07 00:58 UTC — Implemented a native test-only C adapter for the missing
Berkeley DB db_repsite program, using actual frozen library calls and unchanged
upstream test assertions (ADR-0068). The first three multiprocess cases passed;
started the complete eleven-case group separately. Other-repmgr and original
replication tests continue. H07 remains 124 accepted packages and foundation 38%.


2026-11-07 01:01 UTC — Completed all eleven native multiprocess Berkeley DB
cases and five real error-path checks. Prepared the pinned test-only helper in
fresh/recovery recipes; replayed its compile command and got the identical tested
binary. Froze the repmgr007 timing patch, validated both fixture corrections
against 483 files with six rejection cases, and regenerated the 157-input source
notice inventory. Active standard-suite inputs remain unchanged; other_repmgr
and the complete corrected suite are still required.


2026-11-07 — Reviewed corrected Berkeley DB recovery through package staging.
Included the new patch in package provenance and external C/Tcl inputs in recipe
hashes, with a focused regression. Added a production-stage refusal for the
native test helper. No running build inputs or installed target files changed.


2026-11-07 01:08 UTC — Completed the entire twenty-case other_repmgr group,
including membership removal/rejoin and persistent data checks. Combined with
the eleven passing multi-process cases, the two known failures now have complete
isolated group verification. Original full standard execution remains active;
no suite/package acceptance was granted. Preparing a single success-gated
continuation that preserves terminal evidence and refuses unknown failures or
installed changes before syncing corrected inputs.


2026-11-07 01:26 UTC — Started the corrected complete DB suite in a measured
private PID/IPC/network/mount view while the known-failed original collects
later results. Corrected a shared-memory filesystem mismatch and preserved its
interrupted attempt; native C tests then passed and corrected run_std advanced
to Env012. Disarmed the earlier waiting serial-retry supervisor to prevent a
redundant run. Both full-suite results and production acceptance remain pending.


2026-11-07 01:40 UTC — Added independent complete BDB result validation,
including protected evidence, actual exits, frozen source membership and strict
terminal summaries. Actual guest rejection probes pass; fixture hash-map
validation passes for 483 files with six negative cases. Preserved content-
addressed report generations for future fixture probes. Original recovery and
corrected file-operation tests continue; no suite or package was accepted.


2026-11-07 — Prepared the verified-result production handoff while both native
standard suites continue. Preserved exact existing complete-test/production
commands in separate scripts, retained normal runner auditing and native
transaction/reopen/rollback postchecks, and added protected original-failure
archival/nomination. Actual guest probes refuse premature preparation and
out-of-dispatcher consumption. Positive handoff and package acceptance remain
pending. The previous verifier/status commit passed all three published checks.


2026-11-07 — Found and corrected the prepared APT runtime seccomp omission.
Added an observer to the real HTTPS repository install; inherited filters alone
cannot satisfy it. Eight native process/filter scenarios and the exact TLS
fixture passed. Full APT acquisition remains pending. Berkeley DB continues
without active-input changes, and H07 remains 124 accepted packages.


2026-11-07 — Implemented optional QA removal through native Dpkg in private
image staging. A configured 22-package runtime retained all 3,943 Python core
files/links after removing 5,396 QA entries; runtime imports/SQLite and the Dpkg
audit passed. A separate untracked-remnant image correctly failed despite purge
exit 0. Seven new refusal cases passed. Broader marker scanning found six OpenSSL
manual examples in addition to the known 15 Python QA fixtures; source/archive
and native-parser checks classify only those exact documentation bytes as format
placeholders. Raw findings remain reported. Full image assembly remains pending.

2026-11-07 — Integrated ADR-0071's exact manual classification into a gated
staged-image marker review. An actual eleven-package native root retained and
qualified six manual findings; nine negative cases passed, including a real
generated Ed25519 private key and a premature production CLI. Full native logs
and results are preserved, and the installed builder remained unchanged. All
154 local checks pass. This does not accept the complete credential audit or ISO.

2026-11-07 02:15 UTC — Both Berkeley DB drivers remain live with verified process
identities and no terminal exits. Original recovery reached Recd012, iteration 43,
with the same two known failures; the corrected full suite reached Fop008.103
without FAIL entries. No duplicate build or active-input synchronization occurred.


2026-11-07 — Composed fresh native root assembly with an exclusive build lock,
shared Dpkg read transaction, staged reports and separate H10/H11 profiles
(ADR-0072). Independent payload checks verified 19,170 owned entries in an
actual eleven-package private root and rejected ten corruption/refusal cases.
Both premature production profiles and six unsafe output layouts were refused.
Actual source readiness preserved its failed journal at the known H07 Info-index
obligation; no complete image or later milestone was accepted. Installed source
state and the two running Berkeley suites were left unchanged.


2026-11-07 — Added explicit image-state attribution to the prepared assembler
(ADR-0073). An actual eleven-package private root with fresh accounts passed
all 19,214 path declarations and 686 native hardlink groups. Ten altered-state
cases failed as expected; existing payload and marker checks still pass. Native
Tar input-manifest preservation and the fifteen declared Systemd links were
independently verified. Full assembly readiness remains correctly refused by
unfinished H07 metadata; no later milestone or boot acceptance was granted.

2026-11-07 — Added native image loader/shebang availability checks (ADR-0074).
The first eleven-package marker fixture correctly exposed absent Coreutils/env
and Libxcrypt; H07 metadata closure remains necessary. Corrected the comparator's
overly narrow interpreter alias assumption using actual Glibc headers. A fresh
seventeen-package root then passed 147 dynamic executable entries, 41 scripts and
eight refusal cases, with the installed builder unchanged. Full assembly stays
gated on H07-H09; component readiness is not milestone acceptance.

2026-11-07 — Built frozen Squashfs 4.7.5 privately with native tools; gzip/xz/zstd
metadata roundtrips passed. The first real Squashfs-lower overlay experiment found
an ACL restore failure hidden by the ext4-lower fixture. Diagnosed the frozen
kernel implementation, added targeted unchanged-mode copy-up, and verified ACLs,
default inheritance, capabilities, hardlink writes, privileges and bad-path
refusals (ADR-0075). Updated native initramfs archive checks pass. No package or
milestone was accepted from this private preparation; both Berkeley runs remain
active. Correction (ADR-0079): original was in the final matrix, corrected
was in partition (18/27), without FAIL entries.

2026-11-07 — Prepared gated root compression and independent native full
extraction/ACL restoration comparison (ADR-0076). The actual metadata fixture
passes twice with identical compressed bytes; fourteen corruptions/refusals are
detected, including required superblock features. Both premature compression
profiles refuse, and full assembly readiness still stops at H07's shared Info
index. Both Berkeley drivers remain live; corrected suite reached Test142 hash/
partition callback without FAIL entries. No milestone acceptance was inferred.

2026-11-07 — Built the frozen shared Libburnia stack privately with native tools
(ADR-0077). Actual experiments exposed an obsolete xattr header probe and missing
symlink metadata restoration; corrected both without dropping comparisons. Eight
ISO fixture entries, ACLs, hardlinks, numeric owners, dangling/outside links and
corruption rejection passed. All thirteen driver stages exited zero. No package
or milestone was accepted. Correction (ADR-0079): original was in block 27/27;
corrected was in compression (19/27), not the final matrix.

2026-11-07 — Built frozen Mtools privately and passed genuine EFI FAT copy/readback,
UTF-8 names and malformed-image refusal. Native media assembly exposed the
unconditional Apple font-label dependency in grub-mkrescue. Selected explicit
x86_64 BIOS/EFI composition from its frozen implementation (ADR-0078). First
actual boot caught a missing echo module; corrected it and passed all four
BIOS/UEFI CD-ROM/USB loader boots with exact serial/data markers and clean halts.
No kernel/rootfs or later milestone was accepted. The same Berkeley drivers
remain live, corrected with zero FAIL entries.

2026-11-07 — Found and corrected overstated progress for the complete corrected
Berkeley suite (ADR-0079). Test names repeat across groups; the case-only observer
did not identify the outer dispatcher. Actual standard.log shows original 27/27
(hash 8/9) and corrected 19/27 (compression), both live. Added a source-qualified
read-only observer and four regressions, retained full headers/evidence and
corrected the public snapshot and historical narrative. No test or acceptance
criterion was changed; the full corrected result remains required.

2026-11-07 — Added independent fresh-image authentication/identity audit
(ADR-0080). A private eleven-package native image passes; eighteen deliberately
invalid states fail without exporting their contents, including authentication
that the attribution plan explicitly declares. Corrected a DBus-alias setup
assumption in the probe and preserved its failure. Existing marker/payload/
attribution regressions still pass. Full image and boot acceptance remain open.
At 08:48 UTC both Berkeley drivers were live: corrected group 20/27 automated
repmgr with zero FAIL entries; original group 27/hash method 8/9, Test044 cycle 2,
with the same two known failures. No terminal exits; H07 remains 124/126.

2026-11-07 — Bound initramfs creation to the actual compressed generation
(ADR-0081), fixing the H10-only CLI and independently supplied digest/epoch.
Native thirteen-entry compression/readback and 45-entry archive integration
passed, including sixteen binding negatives and fourteen existing compression
negatives. Both actual production profiles remain correctly gated. The assembly
journal in the component experiment is explicitly a metadata fixture; no full
foundation or boot acceptance is claimed. At 08:56 UTC corrected Berkeley is
still live in group 20/27, zero FAIL entries; original is hash 8/9, Test044 cycle 3,
with the same two failures. No terminal exits; H07 remains 124/126.

2026-11-07 09:03 UTC — Verified continued DB progress: original final matrix
hash method 8/9 has reached Test097 after all three Test044 recovery cycles;
corrected other_repmgr group 21/27 reached Repmgr025.h with no FAIL entries.
Fixed stale configuration details in the read-only observer and added two
regressions (ADR-0079). Both drivers are live; terminal results remain pending.

2026-11-07 — Shared native hybrid composition between the actual four-mode
loader probe and prepared H11 CLI (ADR-0082). All four BIOS/UEFI CD/USB probes
passed, plus seven composition rejections. Actual compression/initramfs input
verification adds six negatives; native GRUB ownership and premature production
gate checks pass. Full foundation assembly, native kernel boot and release
acceptance remain pending. No live Berkeley inputs were synchronized.

2026-11-07 09:20 UTC — Original Berkeley suite terminated exit 1 with zero
installed changes. Diagnosed additional final-output rejection: thirteen
Test142 informational-spacing lines and ten missing-recovery-record warnings,
besides the two known failures. Four actual native Tcl controls distinguish
formatting from real failures/coverage warnings without editing the sources or
reports. Corrected suite is live at replication 23/27 with zero FAIL entries,
but its shared formatting defect also needs resolution before strict acceptance.
Published the newly discovered blocker; no acceptance condition was relaxed.

2026-11-07 09:29 UTC — Completed native log-coverage/recovery diagnosis
(ADR-0083): actual exits 0/0, all ten warning-named record types observed,
unmodified original test assertions plus real disk and named-memory recovery
comparisons passed. Corrected and retained diagnostic setup failures rather
than suppressing assertions. Full corrected standard run remains active and
unaccepted; no production gate or raw exit was changed.

2026-11-07 09:40 UTC — Implemented independent complete-output reconciliation
and exact recovery-witness verification (ADR-0084). Native Tcl reproduced all
25 original diagnostics and retained both real failures; incomplete corrected
review and premature production handoff were refused. Bound all 10,208 witness
inputs and passed sixteen rejection cases. Original-history validation now
pins the actual diagnosed terminal reports. Corrected suite advances through
Rep036 in 23/27 with zero FAIL. Full review/qualification and installation remain
pending; strict success semantics and all raw exits remain unchanged.


### 2026-11-07 — Private native kernel compilation started

The preceding status turn was a verified wait: corrected Berkeley PID 1107192
was live in replication at Rep041, zero FAIL, no terminal exits. CI and Pages
for 5849afe passed; exact published HTML matched SHA-256
d92496988b1172eebd50e6e15ee510d9599f504aeb988ea83833995d65de57ad.

Read the frozen LFS 13.1-systemd section 10.3 and extended private kernel
preparation into a durable native build (ADR-0085). Actual free resources
supported two make jobs. Fresh extraction/configuration passed with native GCC
16.2.0 and release 7.1.8-toddy; object compilation is running. Native duplicate
start/resume refusals passed. No shared build-input synchronization, installed
package mutation, boot sector operation or builder reboot was performed.

At 09:50 UTC the database suite was still live at Rep061.a, replication 23/27,
zero FAIL. H07 remains 124/126; final kernel packaging and boot remain gated.


Prepared the next private kernel diagnostic boot while compilation continues.
Native static C compilation and non-PID-1 refusal passed; the actual launcher
refused the unfinished kernel before any QEMU guest was created. This prepares
real BIOS/UEFI kernel/module/namespace checks without accepting a foundation
boot. All complete-Systemd/live-media gates remain unchanged (ADR-0085).


### 2026-11-07 10:03 UTC — Native kernel and two diagnostic boots passed

The private native kernel completed source/configuration/build/private modules/
artifact stages with all actual exits zero. It produced a 15,553,536-byte image
and 20 modules. The durable watcher then ran separate diskless BIOS/UEFI guests;
actual serial/QEMU evidence confirms 7.1.8-toddy boot, volatile data roundtrip,
namespace creation and dummy module insertion/removal. Both powered off cleanly
with exit zero. Driver/supervisor exits and artifact/log hashes were inspected,
and only the test-owned containers were removed. See H09-private-kernel evidence.

The original builder and corrected Berkeley suite were preserved. At 10:03 UTC
the latter was still live at Rep092.d, replication 23/27, zero FAIL. No final
kernel package, Systemd/root/ISO acceptance or milestone credit was added;
H07 remains 124/126. Production package prerequisites and H13 owner review remain.


### 2026-11-07 10:12 UTC — Protect completed coverage while full suite advances

The preceding goal turn made concrete progress: native kernel compilation and
real BIOS/UEFI diagnostic boots passed and were published. Reinspection found
clean Git and the corrected Berkeley process still live. Implemented and ran
root-private custody transfer for the completed native coverage generation;
source/report bytes and actual results stayed unchanged. Real held-descriptor
refusal, tester access denial and idempotent receipt verification passed.
Corrected an absent-runuser assumption using native UID/GID switching. Integrated
the read-only custody proof into full review; active full-suite refusal remains.
See ADR-0086. No original full-test input or production package was changed.

The full standard run advanced through replication/security into recovery,
Recd001.e, block 25/27, with zero FAIL and no terminal exits at observation.
H07 remains 124/126; strict-summary/full-source custody/fresh-build handling and
APT/final closure remain pending. 165 local checks pass.


### 2026-11-07 10:23 UTC — Prepare exact terminal qualification

The preceding turn changed authoritative custody state and verified native
access/descriptor boundaries; it was progress. Current Git was clean and the
corrected standard driver remained live. Prepared the separate complete-run
qualification under ADR-0087: full native review, exact known diagnostics,
protected coverage, full-source custody and preserved raw exits/summary. The
production handoff remains strict until an actual complete positive result.
Native live/focused-run refusals wrote no full qualification/custody state and
left active metadata unchanged. Shared private record publication is atomic and
non-overwriting; actual native checks and 168 local tests passed. No mock result
was substituted for the pending complete native execution.

The current fresh Berkeley recipe still needs private namespace/diagnostic and
portable manifest integration; recorded that concrete remaining build defect
instead of claiming the current recovery profile is a verified fresh rebuild.
At observation the full suite was in Recd002.c, recovery 25/27, zero FAIL. H07
remains 124/126, with APT and all final closure/checkpoint requirements pending.


### 2026-11-07 10:29 UTC — Verify deferred review dependencies privately

Confirmed the shared build-input deployment lacks the later frozen repmgr007
patch/lock row and new review modules. Preserved that active-input boundary.
A private reference preflight using committed metadata and verified patch bytes
passed all 483 Tcl and 460 native seed comparisons without modifying shared
archives or the active fixture. The documented quiescent sync remains the exact
next deployment step after genuine termination. See ADR-0087 for raw hashes.

The full producer remains live at Recd003.i, recovery 25/27, zero FAIL and no
terminal exits. No complete positive qualification or production nomination has
occurred; H07 is still 124/126. Fresh-build portability remains implementation
work, and full release acceptance remains unachieved.

### 2026-11-07 10:39 UTC — Version native DB test preparation

The previous status-only turn verified the specific live full producer; it was
a verified wait. This turn replaces the ignored launcher's temporary-source
preparation dependency with a versioned factory. Actual private preparation
passed with completed native inputs, all 483 Tcl/460 checkpoint matches and
measured namespace/tmpfs isolation. It excludes previous outputs and preserves
raw/protected source evidence. Outside/uncorrected source refusals passed.
See ADR-0088 for exact artifacts/hashes and remaining fresh-recipe integration.
No duplicate suite, production nomination or package installation was started.

At 10:36 UTC the same complete producer remained live in recovery 25/27,
Recd003.k, zero FAIL and no terminal exits. H07/G1 remain incomplete. Continue
portable runner/result integration independently, and inspect the genuine full
terminal outcome before qualification/handoff and APT.

### 2026-11-07 10:46 UTC — Rebuild native DB inputs and verify provenance

The preceding turn implemented and natively verified private preparation; it
was progress. This turn staged the common native test recipe, rebuilt its inputs
from frozen archives in a private canonical-path view with -j2, and verified all
five actual zero exits plus C tests/helper/preparation. The new provenance gate
binds logs, reviewed recipes, native package context, 483 Tcl references and
10,207 native input files to the prepared execution manifest. It never accepts
run_std. Native concurrent/completed/wrong-source/changed-recipe refusals passed.
Fixed host refusal stderr presentation after a concrete observation failure.

The independent build is now terminal and its evidence is retained (ADR-0089).
No duplicate complete database suite was started. The same full producer advanced
to Recd011.b, recovery 25/27, zero FAIL. Portable full-result/coverage integration,
original full terminal acceptance, production and APT/final closure remain.

Fresh-versus-running comparison after compilation: all 460 native checkpoint
entries and the shared library/helper/configuration match. Only four static
archive paths differ among 10,207 inputs; actual native ar confirms identical
member names/order and all 252/266 member payloads. Preserved the differing raw
archives and recorded evidence in ADR-0089; no whole-build byte-identity claim
or full-suite acceptance was inferred.

### 2026-11-07 10:55 UTC — Separate fresh and historical standard provenance

The preceding turn rebuilt native inputs and verified actual provenance/archive
comparisons; it was progress. This turn factors common result checks while
preserving the historical seed and adds explicit fresh compile/input binding,
strict raw-zero success and complete ordered dispatch. Actual native fresh-build
verification and five premature/mismatched result refusals passed; historical
coverage custody still verifies unchanged. No full qualification or source
metadata was changed. Fixed an isolated test import-path error; 173 checks pass.

The actual full suite progressed to recovery's rbtree variant, Recd001.f, zero
FAIL and no exits. Case numbering restarts per method. Portable failed-summary
coverage/qualification and normal fresh dispatcher integration remain the next
independent slice; complete native positive acceptance is still pending.

### 2026-11-07 11:04 UTC — Preserve source custody through production builds

The preceding status reply inspected the actual live full driver and elapsed
time; it was a verified wait. This turn identified a real pending handoff defect:
writable production output inside the tested tree would invalidate source
custody. Implemented a read-only source/separate-output view and shared staged
production/postcheck scripts, keeping the full acceptance gate unchanged.

The actual private production build completed all five stages with exit zero.
Transaction/abort/reopen/persistence checks passed with the staged production
library. Native EROFS, writable separate output, preserved caller stdin, three
invalid-target refusals and unchanged 10,606-entry source snapshots passed.
No package installer or new full suite ran. See ADR-0091 for durable evidence.

The current full driver continues in recovery's rbtree -recnum variant,
Recd011.b, zero FAIL. Portable failed-summary coverage/qualification and fresh
full-dispatch integration remain the next independent tasks while it completes.

### 2026-11-07 — Adopt approved focused delivery and test actual APT consumer

The owner explicitly approved focused Berkeley validation. Recorded ADR-0092,
updated the current delivery policy, stopped only the identified full-suite
process group and preserved actual interrupted exits/raw reports. The earlier
full suite remains incomplete. Added focused clean-build and verified-native
recovery recipes while retaining optional strict full-suite machinery.

Native production crash recovery passed. APT compiled 466 actions and passed
142 tests; fixed a wrong observer binary-path expectation without repeating the
build. Actual cache create/reopen/refresh and SIGKILL/rebuild passed. Corruption
revealed upstream zero-exit error diagnostics: inspected frozen writer code,
required explicit diagnostic rejection before publication, retained the failed
probe and verified the corrected consumer test. Guarded installed BDB/APT and
signed-repository/HTTPS/final closure remain next, with H07 still incomplete.

The guarded focused production recipe and installed postcheck both completed
with exit zero. The actual configured inventory is now 125 packages; Berkeley's
library hash matches the private tested profile. Started the existing final-base
driver for APT and subsequent closure. No suite failure was relabeled successful.

### 2026-11-07 — Complete installed APT acceptance; enter final H07 closure

The actual installed APT exposed a disposable server TLS shutdown defect and a
separate version-check SIGPIPE race. Preserved both failed postchecks, corrected
their causes, verified the installed archive/full payload and repeated all tests
without rebuilding. All 142 unit tests and signed-repository/dependency/upgrade/
conffile/tamper/HTTPS/sandbox/cache/recovery/remove/purge checks passed. There are
now 126 accepted native packages. Resumed final-base driver 28080 for metadata/
ownership audits and checkpoint; H07 remains incomplete until those gates pass.

### 2026-11-07 — Preserve numeric owners in metadata extraction

Closure accepted 14 metadata generations before its ownership guard rejected
CMake after an archive account name mapped numeric 101 to target messagebus 18.
Preserved the failed stage and unchanged installed CMake. Native numeric data
extraction corrected the cause under the same ownership policy; CMake's revised
archive/install passed and closure advanced to GCC (30/126 complete). Existing
directory owner retention was separately measured; final explicit reviewed
build-directory reconciliation is prepared and awaits the serial closure.

### 2026-11-07 — Recover exact dependencies without changing compiled payloads

Closure exposed stale equality pins at Glibc-locales and GCC. Preserved the failed
unconfigured locale generation, implemented provider ordering and same-baseline
exact-pin retargeting, and verified native new revisions +toddy2 configure
successfully. Actual GCC executable and locale archive hashes remain identical
to their original accepted builds; the failed locale record remains unaccepted.
177 local tests pass. Serial closure continued to 43/126 current receipts and
will run the prepared directory identity reconciliation and eight final audits.

All 126 metadata generations and eight final audits passed. Dpkg audit is empty,
APT dependency consistency passed and only the explicitly qualified Systemd
private loader context remains. Directory reconciliation changed exactly the
measured CMake directory, then verified all 2,928 owned directories. Exported
and verified all native archives/records; the builder powered down cleanly and
the final paired cold checkpoint copy/hash/qcow2 verification chain is running.

### 2026-11-07 — Accept H07 and start H08

Both final working-disk copies matched their source hashes and independent qcow2
verification passed. The builder restarted, target mounts were restored, Dpkg
audit remained empty and APT consistency passed. H07 is accepted with its full
native evidence and owner-approved Berkeley coverage qualification; foundation
credit is now 62%. Read frozen chapter 9/10.2 and the prepared H08 recipes. Clarified
that disabling wait-online while using networkd is Toddy's documented offline
policy deviation, not the book's conditional advice for not using networkd.
Marked H08 in_progress for actual target configuration. G1/H13 still require
native foundation boot/live-media evidence; no B story starts before owner review.

## 2026-11-07 — H08 configuration accepted; H09 started

Native H08 driver/recipe/postcheck all exited zero. Recorded 127 installed
packages, exact identity/locale/filesystem/service checks, zero ownership
findings and retained bootstrap backups in docs/evidence/H08.md. Actual boot
networking remains pending. Read frozen LFS 13.1-systemd sections 10.3/10.4
and ADR-0046/0085; start production kernel/configuration through the guarded
driver, preserving prior private builds. Do not perform boot-sector writes
until kernel/configuration results and recovery boundaries are checked.

## 2026-11-07 — H09 accepted; complete live assembly begins

Production kernel/config/loader recipes passed 0/0. Both actual native BIOS/UEFI
boots passed Systemd, C and Kmod checks and powered off with unchanged backing
hashes. Verified h09-boot-ready and restarted the builder; accepted H09 and
started H10. ADR-0096 resolves the prepared media-tool dependency cycle while
retaining separate H10 validation and H11 release profiles. Native console
validation is prepared; no live/ISO acceptance is claimed yet.

H10 media dependencies all passed actual 0/0 recipe/postchecks: Squashfs 4.7.5,
Mtools 4.0.50 and libburn/libisofs/libisoburn 1.5.8 (selected pl02 revisions).
There are 134 configured packages and no Dpkg audit findings. Evidence:
docs/evidence/H10-media-tools.json. Full live assembly/boot remains unaccepted.

H10 fresh-root integration caught missing transfer of its public account
baseline, then missing runtime /dev/null for native install-info. Both causes
were corrected; failed logs and the complete partial root are preserved. The
empty-device-tree native Info regression passed. Removed only the optional
Tk frontend from the ISO CLI package: all 41 retained entries and source
identities match; actual native library/ISO checks passed again. Retrying the
full image without rebuilding accepted libraries or accepting partial output.

The next full-root attempt passed Info generation, ownership and attribution.
Runtime auditing found a root-boundary classification defect, not 82 missing
libraries: nested package directories named tools/sources were rejected. Corrected
that predicate and added canonical/resolved-path regressions (ADR-0099). All
180 local tests pass. Actual full-image runtime retry is running separately;
original failures remain preserved and no live boot is accepted yet.

Corrected complete native runtime audit passed with zero findings: 791 dynamic
executables and 383 scripts. Preserved the failed generation and distinct retry
report under sources/recovery/h10-runtime-path-20261107. Start a fresh full
assembly under the production lock; no package rebuild is needed.

## 2026-11-07 — H10 accepted; H11 release preparation starts

The full 134-package root passed all 18 assembly stages. Compression/readback
preserved 82,011 entries and 1,123 hardlink groups. The protected media-only
continuation generated a bound initramfs and 1,123,698,688-byte validation ISO.
Actual BIOS/CD login, volatile writes, C, Kmod, package checks and DHCP/DNS passed;
QEMU powered off zero and the ISO remained unchanged. Preserve the read-only
lower-loop shutdown warning as a qualification. H10 is complete; H11 is active.
The final release profile still requires optional QA removal and complete image
credential/component review. H12 must test the final artifact, not reuse this
validation ISO as final acceptance. Owner testing remains after H13, before B01.

## 2026-11-07 — H11 accepted; final-media H12 begins

The fresh release root passed all 20 stages and native media drivers ended zero.
Independent SHA/source/component/credential review accepted the 1,094,998,016-byte
hybrid ISO with 134 components and 142 corresponding source inputs. Exact public
QA and source-derived format-marker handling retained original failure evidence.
H12 now tests this final artifact; the earlier validation ISO is not substituted.
G1 and physical hardware remain pending. No Phase 2 execution is authorized yet.

## 2026-11-07 — Final ISO firmware and recovery tests pass

The actual first USB boot exposed missing whole-disk enumeration. Its corrected
initramfs/media generation preserves the same accepted 134-package root. All four
BIOS/UEFI CD/USB boots now pass, including offline USB. GRUB rescue, missing media,
corrupted Squashfs rejection and subsequent intact-ISO boot pass. Final-image
XML enumeration and actual unprivileged live DBus rejection checks also pass.
H12 remains active for native libc follow-ups: Systemd namespaces passed, while
Glibc's initial make-based retry failed on a quarantined bootstrap AR path. Its
complete original report was recovered unchanged. ADR-0102 preserves precompiled
binary identity and original upstream invocation semantics for the corrected run.

## 2026-11-07 — H12 accepted; H13 delivery audit active

All 50 native follow-up tests passed together after restoring the correct mutable
fixture between UID contexts. Cold backing and test binaries remain unchanged;
libc/loader/Systemd hashes match the final ISO image manifest. The four final
firmware/media boots, three recovery cases, intact reboot, XML bounds and required
EN/PT checks passed. Earlier failed/unsupported outcomes remain preserved.
H12 is complete; foundation progress is 96%. H13 exports the exact artifact,
source bundle and test evidence before G1 acceptance and owner review.

## 2026-11-07 — H13/G1 foundation delivered for owner testing

Audited every G1 criterion against actual H01-H12 evidence and exact final ISO.
Exported/read back 142 corresponding sources, 134 component records/notices,
612 build files and 114 raw evidence files. The owner-guide stdio command passed
two real console sessions: network, C, package checks, zero failed services,
volatile-file reset and graceful poweroff; media unchanged. Original upstream
qualifications remain explicit. Foundation 100%, agentic 0%; the complete release
is unfinished. Await the owner's test and explicit approval before B01-B13.

## 2026-11-07 — GitHub Release draft prepared

Created draft prerelease `v0.1.0-foundation.1` targeting the exact H13 accepted
source commit. Uploaded seven selected candidate assets: final ISO, 142-source
archive, source/component inventories, source checksums, source history and a
release-specific SHA256SUMS. GitHub's sizes/digests matched and every asset was
downloaded again with identical SHA-256. Raw local logs remain outside the
release. D10 original-project licensing remains a required owner decision before
public binary publication; B01 still awaits separate owner approval.

## 2026-11-07 — Original-material licenses approved

The owner explicitly approved MIT for original code and CC BY 4.0 for original
documentation/artwork, with third-party terms preserved. Scoped license files,
attribution guidance and ADR-0104 now record D10. The original tested ISO hash
and G1 result remain unchanged. Retarget the GitHub draft to a source commit
containing these grants before publishing; B01 approval remains a separate gate.

## 2026-11-07 — Public foundation prerelease verified

Published v0.1.0-foundation.1 with ten assets and release-specific checksums.
The tag points to the licensed source commit; the unchanged ISO remains bound to
its original tested build commit. GitHub asset digests/sizes, full draft downloads,
public checksum download, public ISO route and tag commit were verified. This is a
VM-only command-line G1 prerelease. B01-B13 remain unstarted until separate owner
approval; G2 and physical hardware are pending.


## 2026-11-07 — Phase 2 replanned for native Toddy and owner previews

Replaced the active Phase 2 PRD/stories/status acceptance rather than retaining
conflicting drafts. Added a detailed execution plan and focused validation matrix,
preferred replaceable Pi/native GNOME architecture, API/local/later setup, optional
OpenCode/VS Code, compatible third-party driver/firmware choices and realistic
humorous installer scenes. The owner requests small traceable commits, basic
working tests and broader validation during use; ADR-0105 records that scope.
Guest implementation remains unstarted. Current work continues with navy brand,
UI concept and public Pages redesign; original logo and G1 artifact are preserved.

Planning checkpoint: make dashboard, planning/link/dependency checks and all 184
existing repository unit checks passed (0.172 seconds as reported by unittest).
See docs/evidence/phase2-replanning.md. No OS build or hardware claim is involved.


## 2026-11-07 — User-customizable harness added before implementation

The owner requires a customizable harness and asked for Hermes/OpenClaw patterns.
Reviewed their official profile/workspace/skill/memory documentation; added the
Toddy profile/persona/config/skill contract, per-profile state, atomic revision and
restore, secret-free import/export and independent permission boundaries. Updated
B01/B03-B08/B10/B13 acceptance together with status.json; S24 remains one focused
fixture sequence rather than a large ecosystem test program. No runtime started.

## 2026-11-07 — Navy identity and realistic static Toddy scenes

Generated dark/light/boot navy backgrounds with the built-in image tool; actual
1672x941 outputs are disclosed. Original logo/mascot hashes are unchanged; archived
the beige predecessors and prompt provenance. Added shared navy tokens, four
GNOME-inspired HTML/CSS concepts and a humorous four-scene installer presentation.
Browser inspection and mobile scene/theme/slideshow checks passed. These are
labeled design concepts, not guest runtime acceptance. See navy-brand-preview
verification under docs/evidence; B11 remains unstarted.

## 2026-11-07 — Navy public presentation with selectable experience previews

Replaced the plain dashboard presentation while retaining status.json-driven
progress, story acceptance/evidence and phase filters. Added four selectable
concepts and the installer storytelling link on the existing GitHub Pages site.
The foundation download remains clearly distinct from planned graphics/assistant.
Export uses an explicit asset/UI allowlist; no new framework, hosted service or
telemetry. Existing checks and desktop/mobile browser interactions pass. Final
publication follows this checkpoint; see docs/evidence/navy-pages-preview.md.

Public Pages publication succeeded for 196852e (run 42390489772, deployment
7623671347); live browser verification loaded the new page, selected the assistant
preview and opened its quick-entry concept. Plan, harness, brand and page work
were delivered as separate commits. Follow-up formatting keeps source HTML/CSS
readable, with clean regenerated output and the same 184 passing local checks.
The owner can review the online concepts; no Phase 2 guest build has started.


## 2026-11-07 — Optional Toddy-branded wallpaper companions

The owner requested wallpaper options with the Toddy logo. Generated and inspected
dark/light right-aligned mascot variants from the existing navy backgrounds and
approved mascot reference. Actual outputs are 1672x941 PNG. These are generated
reproductions; protected logo/mascot source hashes remain unchanged, and plain
wallpapers stay available. Prompts, dimensions and hashes are recorded in the
brand metadata. Public gallery/download integration follows this asset checkpoint.

Branded wallpaper gallery added to the public page with full-size PNG downloads
and retained plain versions. Explicit export allowlist updated for the two assets.
Desktop/mobile gallery checks, source identity hashes and make check passed
(184 local checks, 0.174 seconds). See docs/evidence/navy-brand-preview.md.

## 2026-11-07 — Six-language portal, independent author and preview releases

The owner requested browser-language detection, manual language selection and
four more languages including Japanese, Chinese and Russian. Added English,
Portuguese, Spanish, Simplified Chinese, Japanese and Russian local resources,
remembered preference, shareable lang query and storage-unavailable fallback.
Independent authorship (Marcos Araujo), experimental-preview status and the road
to version 1.0 now accompany actual release/history links without a promised date.
Technical source criteria/docs and simulated OS artwork remain labeled English.

Corrected GNOME concepts to use unmodified real GNOME/Adwaita icons with exact
source/package/commit manifests and retained licenses; recaptured all four PNGs.
Fresh-browser locale/default/override checks, desktop/mobile interactions and the
existing repository suite pass. See public-portal-localization.md in evidence.
PayPal work is pending an owner-supplied public button/link after browser control
failed; no private account data or guessed payment destination was recorded.

The owner chose a single optional supporter-name acknowledgment instead of tiers.
Prepared the translated section backed by public-only config/community.json; no
payment target is guessed, no donor record is auto-published and no special
ownership/software benefits are implied. The PayPal destination remains pending.


## 2026-11-07 — Public portal delivered and release-update rule recorded

The six-language portal, author/release status and real GNOME concepts passed
Pages publication (run 42394817295, bcae8e0) and public HTTP route checks. The owner
then supplied their manually created PayPal hosted identifier WSJKFVXFUULMC.
Configured the standard public donation link and retained the known checkout
verification limit: PayPal blocks the anonymous test browser with HTTP 403 and
account-page tooling cannot read the private page. No account changes or payment
were made. Supporter names remain manually approved and optional.

Added the owner's mandatory per-release portal update rule to AGENTS.md, the
release checklist and development-harness contract. Version/download/checksum,
translated copy, scope/limits and actual Pages verification belong to every
release delivery; this gives no publishing credentials to the installed OS agent.


## 2026-11-07 — Donation CTA suspended after owner checkout failure

The owner reports PayPal's live checkout message: the organization is not
eligible to receive donations. Disabled the public donation link while the
account/product eligibility is investigated using official sources. Preserve
the prior hosted identifier and verification limitations in historical evidence;
do not change PayPal account details or imply a successful payment. Public
supporter acknowledgment remains optional and no names are invented.

## 2026-11-07 — Website mascot yawn and ten localized opinions

Added two generated transparent expression frames while preserving original
logo/mascot hashes. The hero now reacts once to hover, tap or keyboard with a
short bored yawn and one of ten two-line comments in all six portal languages.
Optional frames load only on interaction; reduced motion and decode failure keep
the static original. Added the exact owner-supplied LinkedIn profile to the footer.
Focused desktop/mobile/keyboard/localization/fallback browser checks passed,
along with the 184 existing local checks (0.185 seconds); see website-mascot-yawn
in evidence. The owner handles Patreon for now; no financial profile was changed
and the broken PayPal CTA remains disabled. No OS story acceptance is claimed.

## 2026-11-07 — Correct translated mobile hero clipping

Reproduced the owner's public layout issue with Playwright: Portuguese hero
content exceeded the mobile grid and was clipped even though document scroll
width appeared correct. Corrected track minimums, fluid heading sizing and
translation wrapping. Added deterministic CSS/JS URL versions to the public
export. Thirty viewport/language combinations and image/yawn checks passed;
see evidence/website-responsive-fix.md. No guest development was started.

## 2026-11-07 — Public Patreon support campaign

Added the owner-approved Patreon creator link, official locally hosted symbol,
six-language support campaign, first-post link and optional supporter recognition.
Keep PayPal disabled and avoid invented prices, deadlines or payment options.
Local Playwright responsive checks passed in 24 language/viewport combinations;
Patreon checkout itself remains unverified because Cloudflare blocks automation.
See evidence/website-patreon.md. This is public website work only.

## 2026-11-07 — Remove obsolete PayPal integration

At the owner's request, removed the unused PayPal donation configuration and
renderer. Patreon is the portal's only funding CTA. Historical failure evidence
is retained as history; no public PayPal link or checkout remains.

## 2026-11-07 — Give the public support copy the author's voice

Rewrote the author introduction and Patreon invitation in first person, based on
the owner's stated reason for building Toddy OS and the real dog behind its name.
Replaced generic promotional slogans with concrete work, open progress updates
and an invitation that also welcomes readers without payment. Updated all six
portal locales without changing project scope, pricing or release claims.
Playwright passed 24 locale/viewport combinations (320/390/768/1440), and the
Portuguese campaign screenshot was inspected locally. All 184 checks passed.

## 2026-11-07 — Complete public copy review and dedicated supporter wall

Reviewed every landing section and dynamic preview, simplifying the feature,
installer, wallpaper, roadmap, download and footer copy in six languages while
retaining the approved headline and deliberate mascot reactions. Added a
night-sky supporter page with CSS-only ambient/hover motion and reduced-motion
support. Only approved names in config/community.json drive its generated wall;
a JSON-only edit is sufficient for automatic Pages publication. No private
payment information, invented donors or live financial integration is added.
Basic Playwright checks passed across 48 locale/viewport combinations and all
preview tabs; make check passed 185 tests. See evidence/website-full-copy-and-supporters.md.

## 2026-11-07 — Hundred-name layout demonstration

At the owner's request, added a separate supporter-wall preview with 100 numbered
fictional display names, a localized demonstration notice and noindex metadata.
The real list keeps only Marcos Araujo. A single supporter_preview_count field in
config/community.json controls the demonstration size, capped at 500 names.
Playwright confirmed 100 cards at 320/390/768/1440 pixels without horizontal
overflow and only the approved owner name on the real wall. 185 checks passed.

## 2026-11-07 — Floating-name galaxy and happy Toddy

Replaced name cards with floating text, continuous 3D head orientation, selection
constellations, localized greetings and small bone meteors. Generated a separate
happy website portrait with the built-in image tool and preserved original art.
There are no image/pose swaps during interaction. Fixed local-perspective overlap
and negative-depth touch hit-testing during browser QA. Desktop/mobile/keyboard,
48 locale/viewport combinations and first/middle/last touch selection passed.
See evidence/supporter-galaxy.md for limits and motion/accessibility checks.

## 2026-11-07 — Comet tails and one hundred random thank-yous

Removed the name-to-Toddy connector, gave bone meteors broad tapered light tails,
and added a continuous grateful nod/halo on selection. Added 100 offline random
thank-you lines in all six portal languages, with no immediate repeat and no
image swaps. Fixed caption space prevents name-layout jumps. Playwright checked
all 600 localized responses, rapid/random clicks, native touch, reduced motion
and 48 viewport/locale combinations. 186 checks passed. See
 evidence/supporter-thanks-and-comets.md; no guest/release scope changed.

## 2026-11-07 — Remove superseded website demo and brand duplicates

Removed the temporary hundred-name supporter page, its fake-name generator,
preview-only configuration and localization strings. The only public supporter
wall now comes from approved community names. Removed the obsolete beige v2
background copies/metadata from the checkout and pointed provenance to their
immutable Git history instead. Protected current logo/mascot and navy art remain.
Updated stale community documentation that still mentioned PayPal or name cards.
The linked desktop/installer concept pages remain current product design studies,
not leftover site versions; foundation and release evidence remain traceable.
make check passed 186 tests, including absence of the demo in the clean export.

## 2026-11-07 — Deep editorial pass on the hundred supporter replies

Rewrote all 100 replies in six languages around gratitude and recognizable Toddy
habits. Reviewed EN/PT pairs and made further passes for clarity, warmth, repeated
jokes and standalone random display. Removed ambiguous metaphors, supporter
approval/reward language and dismissive or gross jokes. Added a reusable voice
rubric to ui/README.md. All 600 browser-displayed translations matched; the name,
layout stability and existing random selection remain intact. 186 checks passed.
See evidence/supporter-thanks-editorial-review.md.

## 2026-11-07 — Phase 2 gap review, design closure and resumable execution

Reviewed PRD, all B stories/status dependencies, harness, smoke coverage and
handoff/release instructions. Recorded 17 planning gaps and corrections in
PHASE-2-REVIEW.md, with a risk-first playbook and short continuation card. Closed
owner-level component/IPC/voice/model/sandbox/browser choices in the design
baseline while preserving B01 compatibility locks and actual future runtime gates.
Staged premature S01/S17/S24 checks and added browser/installed-image hygiene
coverage. Synchronized B criteria/dependencies and retained all B states unstarted.

Planning tools now reject B starts without recorded explicit owner approval,
reject story/status drift and preserve an active story while choosing the default
risk-first priority. A rejected CLI B01 start left status.json byte-identical.
make dashboard/site/check passed; 192 local tests ran in 0.206 seconds. These are
repository checks, not guest S01-S26 acceptance. No guest job/model/ISO was started.

The README now links the public site and two clearly labeled current concept
screens. Separate repository-governance evidence records the owner-authorized
main/tag rules, CODEOWNERS, contributor/security policies, fork CI permissions and
secret detection/history audit. Publication checks are recorded after the push.

### Review publication verification

Main a4552ea passed planning/check, public-content and Pages build/deploy; the
CODEOWNERS API reported no errors. The README rendered the transparent mascot
and two labeled concepts on GitHub. A strict redacted history scan exited zero
with no findings (0.921 seconds). Owner-only main/tag control remains active;
Dependabot PR #1 was left for owner review, not merged automatically. The phase
progress command still reports 0% guest Phase 2 and execution approval false.


## 2026-11-07 — Phase 2 execution prework

Prepared native branding package inputs using existing approved art, wallpaper
catalog/default templates, stable application identity and semantic icon roles.
Added 40 EN/PT messages and 10 non-executed scenarios for deterministic UI work.
Audited accepted dependency reuse and heavy new chains; SQLite/FTS5 and existing
build/package tooling need no duplicate stack. ADR-0108 records native branding
without a large Shell theme extension or forced user preference resets.

make check passed 197 tests; temporary desktop-entry validation and strict host
schema dry-run both exited zero without changing host settings. Target integration,
resource measurements and B-story acceptance remain pending. No guest build, model
download or paid API call was started; owner continuation remains false.

## 2026-11-07 — Join installer and boot visual preparation

The owner requested Ubuntu-like installation storytelling and explicitly asked
that prepared parts be joined during implementation. Extended the existing review
surface with boot/completion bookends, lightweight motion and portal translations.
Added native motion inputs and stage ownership, linked from B11/B12 and prework.
Preserved approved artwork and labeled conceptual GNOME imagery. Basic repository
and Playwright checks passed; details in evidence/installer-visual-preparation.md.
No guest implementation, boot engine selection or milestone acceptance implied.


## 2026-11-07 — Resolve five integration prework items

Prepared a non-secret profile/schema/skill example, bounded versioned IPC design
and cancellation/reconciliation fixtures, installation choices, exclusive package
ownership/lifecycle and a short owner validation guide. Incorporated owner offline
clarification: desktop plus setup UI works without agent backend/Node/Pi/executor;
later verified native acquisition requires no OS reinstall. ADR-0109 records it.

Host JSON Schema validator accepted the schema/default and rejected six malformed
config cases. Checked ownership overlaps, input references, offline dependencies,
choice defaults and fixture reconnect consistency. make check passed 197 tests
in 0.212 seconds; no guest runtime proof, build or paid provider/model use occurred.
B stories remain unstarted and owner guest continuation remains false.


## 2026-11-07 — Additional operational prework review

Identified six remaining design ambiguities: safety metadata versus chat history,
session/power lifecycle, unknown provider costs, deferred download trust/network
behavior, version/capability mismatch and opt-in sanitized diagnostics. Selected
concrete defaults in PHASE-2-OPERATIONAL-PREWORK.md and linked owning stories.
Reuse existing smoke gates; no new framework/milestone or expensive matrix.
No guest implementation or runtime acceptance is claimed.


## 2026-11-07 — Unattended execution simulation

Reviewed night execution through nominal and all 13 single-story dependency
faults plus 18 tabletop failure/resumption scenarios. These are structural and
reasoned simulations, not executed guest acceptance. Found/fixed real selector
starvation: a blocked B03 previously won over eligible B02. Added regression for
branch routing and all-blocked visibility without bypassing prerequisites.

Recorded persistent retry fingerprints, bounded diagnosis, selected fallback
authority, long-build monitoring, session/access preflight and end-of-run handoff
in PHASE-2-NIGHT-EXECUTION.md and AGENTS.md. No guest start, autonomous scheduler
or phase approval created. Existing one-writer/safety gates remain enforced.

Validation: make check passed 198 tests in 0.201 seconds; read-only simulation
covered nominal reachability and all 13 single-story faults. Status/approval and
B-story runtime states are unchanged.


## 2026-11-07 — Critical-path bottleneck refinement

Found a concrete scaling hotspot: run_step snapshots/hash-reads the whole target
before/after every recipe. Documented an early timing and safe-equivalence review,
without changing accepted runner safety or claiming measured slowness. Clarified
build/live/offline/acquisition package sets and corrected ambiguous final-image
wording that could accidentally force agent components into offline installs.
Prioritize measured heavy eligible branches and reuse compiled probe packages.
No guest measurements/build/approval or B acceptance were created.


## 2026-11-07 — Approved isolation and change-based validation strategy

Owner accepted isolated builds/staging/controlled transactions and requested a
test-scope decision each interaction. ADR-0110 records prevention versus detection,
maintainer-script/trigger exceptions and required target qualification before
replacing full per-recipe snapshots. AGENTS/validation now distinguish no-change
conversation from affected checks, shared-risk regression and final-image gates.
No sandbox/build implementation or guest-start approval is implied.


## 2026-11-07 — Integrated graphical implementation-readiness review

Owner clarified Phase 2 is a graphical product, not just foundation/backend work.
Reviewed plan after ADR-0110 and closed eight execution gaps: actual native visual
acceptance, GTK/Qt adaptation, non-happy states, UI-loop/render bounds, text/scale,
animation lifecycle, asset export timing and documentation/context overhead.
Linked graphical stories to a scoped interaction checklist; no full UI rerun for
unchanged backend code. Selected paged history/bounded rendering and a short
reading map to avoid repeated whole-plan review. Native timings/proofs remain
pending guest implementation; no runtime acceptance/approval was created.


## 2026-11-07 — Documentation and public-portal synchronization

Checked current docs, handoff, status, story titles and portal against the final
Phase 2 decisions. Updated README/continuation/decision index, clarified historical
H-driver instructions, and synchronized offline/later-assistant copy in all six
portal locales. Renamed B12 to guided offline installation/optional software setup
to remove the misleading implication that installation itself needs an LLM.
The native installer is deterministic; no internet or AI is needed for base install.
No release version, asset bytes, guest approval or acceptance states changed.


Portal Phase 2 copy review additionally clarified Stop versus rollback, separate
customization/permissions, verified optional IDE packaging and deterministic
offline installation. EN plus five translations are synchronized. make dashboard/
site/check and JavaScript syntax checks passed (198 tests). CUA inventory worked
but binding the existing portal tab failed with a tool timeoutMs error; no fresh
visual browser inspection is claimed. Deployment/served-file verification follows.


## 2026-11-07 — Per-story strategy and handoff review

Reviewed all B01-B13 slices/acceptance/prerequisites. Removed avoidable model gate
on executor work: B04 now depends on B01; B05 explicitly joins B03+B04. Fixed
premature B01 native-setup wording, clarified B03 minimal validation versus B05
atomic profiles, and aligned B13 instructions with offline/acquisition roots.
ADR-0111 and PHASE-2-STORY-STRATEGY record tradeoffs and owning proofs.
Structural fault simulation regenerated; focused selector regression covers
B03 blocked -> B04, then B04 blocked -> B02, without bypassing B05 prerequisites.
All B runtime states remain unstarted; no guest approval or execution occurred.


## 2026-11-07 — Shared optional-software catalog preparation

Implemented approved preparation: 28 open candidates, six categories, EN/PT
descriptions, no qualified release artifacts. Git base; Docker/OpenCode optional;
mise excluded. Final installer selection saves intent for installed-user review
and acquisition. Native CLI/core and qualified per-user Flatpak GUI share existing
setup/pending/authorization paths, independent of the agent. Agent recommendations
are on request; essential hardware/model/key/grant flows remain separate.

Added ADR-0112, catalog/lifecycle contract, owning B slices and synchronized B06/B12
criteria/status without changing prerequisites or runtime progress. Added three
semantic scenarios/four messages and three catalog integrity tests. Portal copy
reflects deferred acquisition in all six locales. No binaries, guest build, Flatpak
installation, credential use or guest-start approval was created.

Validation: make dashboard/site/check passed; 201 tests in 0.201 seconds.
Catalog references, six-locale portal copy and unchanged approval/gates/story
statuses/dependencies were checked. Runtime native/Flatpak proof remains pending.

## 2026-11-07 — Final Phase 2 documentation and portal consistency pass

Reviewed active plan, all B-story graph/criteria, prepared contracts, candidate
catalog, README, developer handoff, continuation, generated status and portal.
Removed ambiguous preference for API key entry (now installed-user only), live
extra acquisition and repeated installer framework evaluation. Clarified B13's
base/acquired configurations, surfaced catalog handoff and shortened the resume
card. Public six-language copy now identifies Git in base and Docker/OpenCode/
VS Code as optional only after verified packaging. Regenerated structural evidence
against the current status hash. Existing release remains public experimental
foundation; G1 passed, all B unstarted, G2/physical validation pending.

Protected logo/mascot hashes, 28 unqualified candidates, 44 bilingual messages and
13 semantic fixtures checked. make dashboard/site/check passed; 201 repository
tests, JavaScript syntax and local-reference consistency passed. These are not
native guest or app qualification results. Publication and browser checks follow.


## 2026-11-07 — Owner authorizes isolated Phase 2 implementation

Explicit owner continuation is recorded in ADR-0113 and status.json before B01
starts. Physical foundation testing remains pending. B01 is in_progress without
acceptance credit; first slice inventories the accepted cold post-H13 pair and
creates separate writable overlays over read-only backing storage. No accepted
foundation packages are rebuilt. One guest writer, no subagents/model switching,
bounded diagnosis and affected checks remain required. The planning validator passed, but the first make check exposed two unstarted-fixture
errors after approval changed. The authorization commit was published before this
failure was reviewed. Resetting fixture authorization with fixture milestones fixes
that inconsistency; the corrected 201-test run passes. Clone/runtime evidence will
be recorded separately after execution.


## 2026-11-07 — B01 accepted-foundation disposable clone inventoried

Cold post-H13 builder/target hashes and qcow2 checks passed; new KVM clone writes
only separate overlays, with original images mounted read-only. Actual guarded
native Dpkg audit/APT check passed. Existing full runner scan measured 18.714 s
for 4.56 GB/71,416 regular files. B01-A complete; B01/G2 remain unaccepted.
Four start/access/backing guard regressions pass. Initial boot-readiness SSH
failure received one successful post-boot retry without dispatch/replay.
Next: qualify isolated unprivileged staging, then native dependency/engine spikes.


## 2026-11-07 — B01 isolated native compiler/staging proof

Native UID/GID 101 compiled/staged/ran C with zero effective/permitted capabilities,
no-new-privileges, read-only input/dependencies, absent private roots/sockets and
network denial. One entry-capability/cwd correction passed; failure retained.
This qualifies only the build namespace; optimized native transactions remain
unqualified and keep full-root verification. Official SHA-256 files verified the
BLFS 13.1 GLib/introspection/PyGObject/Node source candidates. GLib bootstrap native
compile/stage exit zero; focused consumer checks are the next result to assess.
Repository make check passed 205 tests; no unchanged foundation suite rerun.


## 2026-11-07 — Pi worker protocol fixture while native Node compiles

Added exact Pi 1.5.0 npm closure, bounded strict JS/Python framing, one sequential
broker-facing tool fixture and D-Bus XML candidate. Host-only real-Pi fixture:
11 cases passed; JS framing 5 groups/Python 6 regressions passed; make check 215
passed. Native worker/bridge and complete notices still pending. Node source
build continues under recorded PID/boot/start identity; no second guest writer.
Status now reports verified B01 slices without awarding milestone credit.


## 2026-11-07 — Native bridge/installer binding probes prepared during Node build

Prepared actual GIO async/peer-UID/typed-signal/sealed-FD/pipe-rejection fixture,
Node native package transaction/postcheck and the next scanner bootstrap recipe.
Only syntax/existing repository checks and the crypto vector were run so far;
these preparations are not native acceptance. The source Calamares 3.4.3 archive
contains Pybind11 2.11.1, so a minimal accepted-Python-3.14 embedding probe is
prepared before committing to Qt compilation. No installer replacement or core
Python upgrade is presumed. Node remains the sole healthy guest writer.


## 2026-11-07 — Success-gated native Node handoff prepared

Added a deterministic host driver which observes the existing Node build without
another guest writer, accepts only actual exit zero with pinned source inputs,
refuses any existing running/failed/success transaction marker, then runs the
reviewed native Node package transaction once. Missing identity, timeout/window
end, changed inputs and nonzero exit perform no handoff. The runner now records
the optional Phase 2 source-lock hash without changing H recipes or evidence.
make check passed 217 tests. Driver result alone is not milestone acceptance;
actual package/marker/postconditions remain mandatory before further dispatch.


## 2026-11-07 — Native Node/Pi and descriptor-safe compiler boundary

Node source build completed once. Install committed; initial missing-procfs
postcheck failed, then the unchanged postcheck passed in corrected native context
without reinstall. Preserve original 0/1 and separate corrected 0/0 records.
Native Pi 1.5.0: 11 cases passed, 0.643 s, peak child RSS 65,912 KiB; JS framing
also passed. Fixed an inherited writable lock FD gap; actual native FD/path/
network/compile and parent-lock barrier proof passed. No optimized transaction
path enabled. Next: native GI/PyGObject/async bridge, then installer no-write spike.


## 2026-11-07 — GLib typelibs and native GIO bridge staged

Installed GLib-owned metadata with unchanged core library bytes, reusing fourteen
checks. PyGObject compiled/staged and actual GIO async/peer/signal/FD boundary
fixture passed. Fixed a session-daemon teardown race after preserving whole-command
exit32; rechecked FD/parent-lock isolation, bridge and actual process cleanup:
exit0/no namespace processes. GTK/Cairo/native desktop not yet tested.
Next: install owned PyGObject package, repeat affected installed binding fixture,
then Calamares/Python no-write compatibility probe. make check217 passed.


## 2026-11-07 — Installed native GIO and Calamares embedding boundary

PyGObject transaction0/0 and installed GIO fixture0 passed. Calamares3.4.3
bundled Pybind11 2.11.1 compiles/links/runs with native Python3.14.10 unchanged;
deprecation warnings recorded. Next: minimal QtBase/Svg/LinguistTools dependencies
for no-write installer feasibility, not final graphical desktop acceptance.


## 2026-11-07 — Native QtBase offscreen package

Qt6.11.2 compile/stage0; native package/postcheck0/0 after reconciling a pre-install
copyright guard failure with changed0. Native offscreen Widgets action/render,
TLS availability, private DBus and Concurrent consumer passed. Font/display/visual
qualification remains pending. Added a one-shot sequential prerequisite controller
with terminal receipts and no retry/replay; no foundation suites repeated.


## 2026-11-07 — Calamares native no-write integration verified

Five minimal prerequisites passed sequential native consumers. Calamares3.4.3
compiles/stages and starts natively; real PythonJob/JobResult executes a synthetic
plan and nine invalid-input cases. Preserved shell/consumer-ABI failures; resumed
only affected consumer, no source rebuild. Raw Boolean map conversion exposed a
typed boundary issue; schema-versioned JSON string/native Boolean checks passed.
ADR-0116 records the selected contract. Final graphical/disk/privilege/boot/package
trust/recovery proof remains B12; B01 final architecture/root/budget freeze next.


## 2026-11-07 — B01 scoped acceptance and exact continuation

All five B01 criteria audited against real native probes and frozen contracts,
not desktop/installation claims. Pinned31 root/shared inputs, legal notice hashes,
scoped GNOME graph (alternative desktop backends excluded), CPU-model/budget and
installed-root account/boot/trust/recovery recipe. Ten native additions and
Calamares/GIO/Pi proofs retained. Source-only candidates stay unqualified until
the owning build/runtime story. Phase2 weighted progress5%; G2/physical pending.
Next B03 by default selector: actual local CPU inference/tool slice, reusing Node.


## 2026-11-07 — B03 native CPU inference boundary

llama-cpp0.9.0 compiled/staged and native package/postcheck0/0. Optional private
loopback namespace containment/parent-lock proof passed with no external route.
Actual Qwen3-1.7B-Q8_0 streamed READY:0.812s health,0.289s first text,2,320,036KiB
peak,4CPU affinity/4threads on development VM. Unauthorized generation401/401,
server shutdown0 and token file removed. No Pi tool task/provider/acquisition
acceptance yet; native Node/Pi/GIO/runtime packages will be reused.


## 2026-11-07 — Real Pi local tool/cancel and per-user runtime

Native8 passed real file-tool task4.29s, active cancellation6ms/new response0.34s,
exact tokenizer context admission0generation, otherUID socket/key EACCES and bearer
401/401, runtime exit0/private cleanup/idempotent Stop. Source hashes and the exact
input contract snapshot retained; final local profile temperature0. Original
failed/stochastic/formatting runs and bounded correction ledger preserved.
B03 local-task criterion passes; provider protocols/acquisition/choices remain.

### B03 native provider protocol fixtures — 2026-11-08 UTC

Qualified four advertised protocol families against actual pinned Pi1.5.0 on
native Node24.19 in the existing no-network namespace. Streaming/tool/usage,
classified errors, no retry/redirect, cancel/deadline and limits passed. All remote
families remain fixture-only/live-unverified. Two synthetic host harness mistakes
were corrected before one native passing job; production provider unchanged.
B03 first criterion accepted; acquisition/choice remains. No package/model rerun.

### B03 accepted; explicit resumable acquisition — 2026-11-08 UTC

Native acquisition-3 ten file/TLS-loopback checks and acquisition-cli-1 passed.
Explicit hash/license/network consent, private partial/Range/final integrity,
unsafe path/conflict/space/concurrency denial and no credential-forwarding tested.
First native fixture environment errors retained and corrected once. Added narrow
HTTPException classification and affected regression. ADR-0118 records scope and
network cancellation timeout. B03 complete in headless scope; B04 next. B05/B06/B12
retain activation/secret/UI/installed integration, no G2 or physical claim.

### B04 independent policy/operation core — 2026-11-08 UTC

B04 started after B01; native policy-core-1 six focused tests passed. Persisted
session/standing expiry/revocation generations, input-bound IDs, serialized effects
and actual child-loss uncertain/no-replay recovery. No root IPC/privileged effect
acceptance yet. Next strict system-D-Bus boundary and independent owner policy
client. Unchanged B03 model/package proofs reused.

### B04 actual native root/user executor boundary — 2026-11-08 UTC

executor-ipc-3 passed root service/UID101 configuration postcondition, acknowledged
root id0, duplicate dispatch and wrongUID/schema/escalation/revoked/policy-read
denials in synthetic root. No installed/etc changed. Native1 missing optional
setpriv corrected with proof-only identity helper; native2 failed exact known GIO
deprecation cleanup, native3 passed after precise classification. All original
exits retained. Owner polkit/logind surface, user tools, Stop and structured
package/service/network remain pending; no B04 criterion marked complete.

### B04 Stop and service-loss recovery — 2026-11-08 UTC

Native executor-ipc-5 passed root Stop86ms/actual child absence, service SIGKILL
with child absence, restart uncertain/no replay and unchanged boundary denials.
Native policy-core-2 eight tests passed, including old-store migration and durable
cancellation. ADR-0119 explains parent-death and unrestricted-root limits; staged
systemd control-group lifecycle remains to prove. User tools/package/service/
network and authenticated owner/logind surface still pending; B04 incomplete.

### B04 active revocation — 2026-11-08 UTC

Extended revoke to persist Stop requests for managed running effects. Native
executor-ipc-6 stopped an actually started root command90ms after revoke, retained
uncertain outcome and denied later dispatch. policy-core-3 eight changed storage
checks passed. Exact source hashes/evidence retained; no B04 completion yet.

### B03 TLS assertion precision — 2026-11-08 UTC

Tightened synthetic CA rejection to actual SSLCertVerificationError with proxies
explicitly disabled. Native acquisition-4 ten affected checks passed; production
download/runtime bytes unchanged. Earlier generic assertion not used as new proof.

### B04 native ordinary tools and FIFO denial — 2026-11-08 UTC

user-tools-1 five actual UID101 filesystem/process tests passed1.113s: exact hash
writes, path/metadata/bounds, clean environment and active Stop/process absence.
Fixed blocking FIFO read before type inspection; executor-ipc-7 tested the affected
root reader and existing boundary/recovery paths, all0. Ordinary tools still need
broker routing; package/service/network and installed owner/systemd remain pending.

### B04 native package transactions — 2026-11-08 UTC

executor-ipc-13 signed toy APT install1/upgrade2/remove preserved owner conffile;
Stop during real postinst waited safe commit, with actual status/audit/version
proof. Unbounded drain/bounded retention prevents a text limit killing native
writes. Original8 control-mode and9/10/11 cache-path failures retained;12 passed,
13 extends maintainer boundary. policy-core-4 nine changed checks passed. ADR-0120
records source-backed APT flags, no product key or final installed-source claim.
Service/network/owner runtime prerequisites still pending; no B04 completion.

### B02 native runtime branch — 2026-11-08 UTC

Preserved B04 verified checkpoint; actual remaining NM/polkit/logind/systemd
integration cannot pass in the current chroot with missing native runtime.
Marked B04 blocked and B02 in_progress, no prerequisite changes or user dependency.
Begin selected XML/Wayland/graphics dependencies, reuse B01 packages and preserve
one guest writer. First native graphical session and all B02 criteria still due.

### B02 first native XML package — 2026-11-08 UTC

libxml2-1 source/stage0 with7 upstream programs/3904 regressions; native owned
2.15.3 install/post0/0 and actual external-loader denial/positive control passed.
Exact notices and source/recipe hashes retained. Full-root scan overhead19.328s
of22.343s measured by wrapper around unchanged runner, no optimization bypass.
Wayland1.26/Protocols1.49 verified against frozen book MD5/official HTTPS and
SHA256-pinned before extraction. Desktop/native GUI still entirely pending.

### B02 private descriptor alias qualification — 2026-11-08 UTC

Added the standard/dev/fd alias needed by Wayland descriptor-leak tests, pointing
to the already exposed private/proc/self/fd. alias-probe-1 proved FD/source write
denial, caps0, outside/egress refusal, native C and actual parent lock held/released.
No global security change or unchanged model/foundation suite rerun. Original
Wayland failure preserved; affected recheck recorded separately.

### B02 native Wayland and protocol packages — 2026-11-08 UTC

Wayland six original+twenty corrected test drivers passed without binary rebuild;
FD alias guard/lock proof passed. Original install0/post1 reconciled postcheck-only
0/0 after reading upstream EGL version18.1/backend3; no reinstall. Native client/
server sync and scanner passed. Protocols1.49 native191 tests/install/post0/0.
Own archives/notices/provenance retained; no GNOME/compositor acceptance yet.

### B02 Pixman native pixel operations — 2026-11-08 UTC

pixman-1 native35 tests/stage0; owned0.46.4 install/post0/0, actual pixel-composite
consumer and notices verified. No optional GTK/PNG/OpenMP dependencies or repeated
old suites. Existing kernel config enables virtual DRM/namespaces/seccomp, not a
hardware test; no kernel rebuild. Next pinned image/font dependencies for GTK.

### B02 native image and font prerequisites — 2026-11-08 UTC

Standard libpng36 tests/installed PNG memory roundtrip, FreeType staged/installed
version+BDF pixels, Fontconfig15 offline drivers/installed XML+PCF match, and
FriBidi8 drivers/installed Hebrew order/maps/levels passed. All owned native
transactions0/0; full-root checks retained, source notices verified. Stock system
PNG serves Cairo/GDK; Firefox bundled PNG remains selected unless APNG qualified.
No repeated foundation/model suites or native GUI acceptance.

Cairo3 registered header/syntax checks and installed pixels/text/PNG/GObject passed.
HarfBuzz original compile stopped on missing FreeType GIR; preserve linked objects
and original failure. The B01 scanner-only bootstrap deliberately omitted data.
Prepare four selected original GI1.86.0 declarative types separately, preserving
qualified scanner/GLib binaries; resume same HarfBuzz graph after actual dependency
installation. No foundation rebuild or global architecture change.

### B02 bounded Pango metric checkpoint — 2026-11-08 UTC

Pango/GI compiled, but original font fixture selection produced3 failed drivers.
Curated full Cantarell fixed ellipsis/empty-line invariants; Boxes hardcoded derived
metrics still failed with and without fallback. Two corrections exhausted for this
cause; all recorded library/test binaries unchanged. No stage/package accepted.
Failure/evidence/next unblock preserved; move to independent Graphene/MIME/pixbuf.
Do not resume the same guesses or mark the remaining assertion passed.

### B02 native vector math and MIME data — 2026-11-08 UTC

Graphene installed0/0 with vec/matrix/GObject/Python proof; source-bundled MuTest
then enabled locally,18 new math drivers0 and prior shared hashes unchanged.
MIME17 native drivers and owned generated cache install/post0/0, GIO TXT/PNG/JSON
passed. Exact official XDGMime commit pinned as test-only source; no compiler
network or repeated old suites. Pango metric slice stays blocked/uninstalled.

### B02 LLVM compiler prerequisite dispatch — 2026-11-08 UTC

ADR0121 records frozen LLVM22.1.8 core/Clang, required Rust poison-select codegen
patch, measured disk reserve and mandatory scoped compiler/JIT validation. Private
256MiB POSIX SHM added only inside compiler namespace; actual child RX execution,
parent invisibility and all existing denial/cap/FD/lock checks passed. LLVM input
verified before extraction/patching,198 recorded source edits (14 upstream patch,
FileCheck install and Python3 shebangs). llvm-1 compiling with4 workers/1 linker;
no stage/install/acceptance yet. Rust source-authenticated stage0 host prefetch is
independent; no second guest writer, no paid service or foundation replacement.

### B02 compiler consumers and GNOME font preparation — 2026-11-08 UTC

Prepared strict LLVM critical-report promotion and installed C++/PIE/SSP/libclang/
ORC/FileCheck consumers; not executed or accepted yet. Authenticated GNOME50
Adwaita fonts50.0 from official SHA256, matching actual schema50.1 family defaults.
Six unmodified TTF files and full OFL1.1 retained; data-only stage, installed
fontconfig matching and separately inventoried generated cache recipes prepared.
Native font qualification pending; no graphical acceptance. Host syntax and
make check247 tests passed. Latest pushed3a833fc has all3 remote workflows green.
llvm-1 continues healthy, latest direct step3494/4451 and35GiB target free.
No second guest writer or repeat of previous suites.

### B02 portable Pango and JPEG preparation — 2026-11-08 UTC

Prepared pango-stage-6 and strict native promotion for ADR0122: require the new
independent oracle0, unchanged binaries,9 original core passes,17 curated font
driver passes and2 empty upstream drivers. Preserve original failed golden;
no native oracle/stage/install accepted yet. Prepared libjpeg-turbo3.2.0 CMake/
CTest JUnit stage and installed JPEG memory consumer with explicit lossy tolerance.
Optional assembler/SIMD disabled; no performance acceptance. Source legal texts
include full IJG README, component terms retained. NASM is outside the selected
graph; source preparer refused it before mutation, no mandatory dependency added.
Host syntax and make check247 passed. d003170 all3 remote workflows green.
Guest llvm-1 remains the only healthy writer; no metadata sync or test replay.

### B02 native Pango/default fonts and completed LLVM compilation — 2026-11-08 UTC

LLVM4451 compilation steps actual0, source-patched22.1.8 X86+AMDGPU confirmed.
One-time guarded controller synchronized metadata only after terminal0, dispatched
new portable Pango oracle:3 native cases0, original binaries unchanged. Stage6
then native Pango install/post0/0 passed Portuguese wrapping/pixels/markup/GI.
Original golden failure remains visible; no old-budget reset or upstream-all-pass
claim. Adwaita50 six original TTFs staged and installed0/0, font matching/cache
passed. Host input-log redirection collision refused before any guest write;
verified absent source/work, preserved empty artifact, corrected invocation once.
Next writer llvm-qualify-2 builds critical test dependencies then seven suites,
no compiler restart. All desktop/runtime criteria remain pending actual GNOME.
Keyboard1.13.2/config2.48 source archives authenticated host-only for later input.

### B02 LLVM runtime/SDK ownership preparation — 2026-11-08 UTC

Actual compiler output names libLLVM.so.22.1 plus relative libLLVM.so alias.
ADR0123 implements existing base/live SDK exclusions before first LLVM package
installation: split these two exact paths into llvm-runtime, preserve library
bytes/notices, make build-only llvm depend on its exact version. Existing native
backend/full-root verification retained; no foundation changes. Three focused
partition fixtures passed (SDK exclusion/bytes, bad alias, existing output refusal),
make check250 passed. Native split/install/ABI and image scope remain pending.
llvm-qualify-2 healthy critical dependency build174/1068; do not restart. Metadata
sync required after its terminal result and before LLVM promotion.

### B02 observer correction and changed-font selection — 2026-11-08 UTC

Monitor70454 exited3 falsely: live-child CPU sums fell as compiler processes
finished, outer output redirected to critical-tests/build.log. Actual Ninja
progress continued. Corrected observer to nonnegative deltas keyed by PID/start
identity and optional explicit private progress-log metadata. Three regressions
passed; replacement monitor89697 observes real writer unchanged, no restart.
Prepared pango-system-fonts-7 for17 font-sensitive drivers because installed
Adwaita changes fallback inputs. Nine core/independent geometry proofs reused;
no full unchanged suite or install replay. Native affected run pending writer.
PAM1.7.2 source cached host-only. Its [official1.7.3 release](https://github.com/linux-pam/linux-pam/releases/tag/v1.7.3)
lists memory/authentication fixes requiring targeted source review before native
privileged integration. Existing [namespace advisory](https://github.com/linux-pam/linux-pam/security/advisories/GHSA-f9p8-gjr4-j9gx)
was fixed before1.7.2; that observation alone is not complete security acceptance.
No guest PAM changes, silent version upgrade or foundation rebuild.

### B02 native compiler-test dependency and affected unit recovery — 2026-11-08 UTC

LLVM critical dependencies1068 steps completed, first lit launch refused missing
psutil before cases. Pinned scoped book psutil7.2.2, isolated offline wheel/stage
and native owned install/post0/0; actual UID101/installed process memory/CPU,
timeout, terminate and recursive child kill/reap passed. Full upstream system/
network matrix not claimed; build-only dependency. Scoped source reader now
selects the exact referenced module section, tested against wrong-first-download
and missing-anchor fixtures. No foundation rebuild.

Resume3 dependency dry-run was no-op;10501 LLVM unit PASS and one relative-path
FAIL from root cwd. ADR0124 preserves raw failure; job4 from normal build cwd
rechecked1646 affected Support cases0, reuses8856 other native passes, no binary
recompile. Clang-unit26497 PASS and Transforms9189 PASS/1592 UNSUPPORTED/38 XFAIL
recorded; other critical suites/stage/install pending. Three negative/merge gate
checks and make check258 passed. Current writer job4/PID156881/monitor79334.

### B02 native LLVM, changed fonts and JPEG — 2026-11-08 UTC

LLVM job4 terminal0, all7 selected suites qualified:55063 PASS/5576 UNSUPPORTED/
61 XFAIL, poison-select PASS,882 compiler/test binaries unchanged. Original unit
failure preserved,1646 affected Support cases rechecked with normal build cwd.
Full raw native reports/receipts preserved in host evidence bundle d19d3021...
53055. Owned separate runtime/SDK install/post0/0 passed C++/PIE/SSP/libclang/
ORC/FileCheck; full-root transaction161.052s. Runtime payload contains only
libLLVM ABI22.1/alias and legal docs; no SDK. Final consumer/image closure pending.
Adwaita changed-input Pango17 drivers0/no binary rebuild. Serif currently maps
to Mono; add an actual proportional serif before browser acceptance. JPEG C
backend upstream CTest/stage and owned native memory pixels install/post0/0.
No native desktop/physical test claimed. Next Rust offline input/compiler slice,
measured target30GiB/host122GiB and existing reserves preserved. b2eb657 all3
remote workflows green. No guest writer or queued continuation remains.

### B02 offline Rust native compiler dispatch — 2026-11-08 UTC

ADR0125 versions the external read-only source config/private build-dir and
source-authenticated official seed installers under private DESTDIR/caps0/no
network. Initial generated remote newline syntax refused before extraction;
verified absent source/work and4 cached archive SHAs, preserved failed log, used
chr(10)/compiled generated programs before RPC. Second input preparation0.

After extraction target24.7GiB was below26GiB compiler gate. Native helper
verified installed LLVM0/0, both canonical archive hashes and exact3 stage
manifests before retiring only duplicate usr/etc stage trees. Archives, source,
882 compiled binaries and raw evidence retained, DEBIAN metadata/retirement
markers preserved; promotion replay blocked. Target26.6GiB at dispatch. Two
unknown/changed-payload safety regressions and make check260 passed. No physical
disk operation, source rebuild or global security change.

Private seed1.96.0 versions/commit/sysroot passed; rustc-1 now compiling actual
Rust1.97.1/compiler LLVM wrapper/crates with4 workers, thin LTO/systemLLVM22.1.8,
source-vendored offline dependencies. No critical Rust tests/stage/install yet.
Current guest jobPID248700/monitor74685, source input rust-toolchain-1.97.1.

### B02 Rust compiler result, standard tests and PAM source preparation — 2026-11-08 UTC

rustc-1 terminal0 after27m40s, native Rust1.97.1/LLVM22.1.8 and real Vec/thread
consumer0. Post-build target21.36GiB. Preserve compiled cache. ADR0127 selects
original core/alloc/std unit/integration tests with source-supported --tests,
private loopback/four threads, raw reports/tool hashes and16GiB reserve. Actual
rustc-std-2 dispatched PID271179, monitor74621; test/stage/install gates pending.
No native graphical acceptance or Phase2 ISO yet.

ADR0126 preserves frozen PAM1.7.2 with nine explicitly sourced ordered patches.
Fresh authenticated host replay0/fuzz0, eight source files match reviewed tree;
algorithm mask uses actual frozen flags, preserves DES/BIGCRYPT/defaults and
quiet/minlen. Original host table fixture7/adapted0,64 transitions. One context
prerequisite, two raw HTTP504 transport attempts and one pre-write adapter guard
failure preserved in ledger; complete official API hunks used for prerequisite.
Exact default/per-file notices retained. Raw fixture/replay evidence bundle and
hash retained for final release. No guest PAM/Shadow/systemd change or native
credential/privilege/session acceptance. GitHub f9cc3b3 scanner download failed
504 before executing; one failed-job rerun now passed, no ignore rule changed.

Native Rust std bootstrap completed:35 libtest drivers6223 PASS/5 upstreamignored
and custom pipe-subprocess sentinel success. Collector wrapper1 afterwards from
removed temporary clippy path preserved; source-backed derived qualification0,
no independently saved native exit/before-after hash claim. Four recovery guard
regressions0. Upstream recreates sysroot; correct collector persistence/retained
artifact paths, no passed-test replay. rustc-compiler-3/PID282672/monitor82919 now
tests original ownership/async/FFI/linkage/editions/Send-Sync compiler suites.

### Public scanner transport recovery — 2026-11-08 UTC

The next public-safety run42469282524 again failed HTTP504 before the scanner
executed. Local redacted history scan passed. Avoid repeated unchanged reruns: add
one official GitHub release API fallback after bounded browser transport, retain
the same pinned8.30.1 asset and mandatory SHA256, read-only job permissions and
redacted scan/approved exact exceptions. Host gh release acquisition succeeded
and matched551f6fc8...f2470eb; corrected remote execution pending. The step uses
only the ephemeral workflow token, never installed product credentials.

### B02 native Rust compiler tests and next stage — 2026-11-08 UTC

rustc-compiler-3 terminal0 after11m50s:1552 PASS/7 upstreamignored/19666 filtered
outside selected ownership/async/FFI/linkage/edition/Send-Sync paths. Actual native
exit saved, launcher hash stable (not full driver/stdlib proof), target20.96GiB.
Original std ignores identified from native --list without rerunning cases; exact
upstream source reasons retained. rustc-stage-4/PID323437/monitor3660 now staging
and qualifying real Cargo/Clippy/Rustfmt/Rustdoc, no owned native install yet.

ADR0128 prepares four unmodified DejaVuSerif2.37 faces for the observed proportional
serif gap. Official GitHub transport504; official SourceForge exact size/SHA0.
Recipes preserve Adwaita/user preferences, full notices, generated cache manifest,
real i/W FreeType spacing and family/style/coverage checks. Native stage/install
and changed-input Pango17 remain pending. Keyboard2.48/libxkbcommon1.13.2 sources
and frozen required upstream patch cached, native pending. Corrected scanner CI
6822bbb all3 workflows passed with unchanged required scanner hash/scan policy.

### Rust stage collector and package guard preparation — 2026-11-08 UTC

Source Cargo0.98.0 renders CLI1.97.0 in cargo/version.rs independently of
rustc1.97.1. Correct canonical tool expectation/persist versions before checks.
Healthy stage4 still uses original probe; preserve it. Host controller60103
waits actual terminal and can dispatch only guarded unprivileged tools recovery5
with successful install0/known assertion/empty original consumer tree and unchanged
stage. No restaging, compiler/std replay or automatic owned install. Reconcile
controller/tools5 before metadata sync. Strict future promotion and actual installed
consumer checks prepared; not executed or accepted. Native dependencies queried
read-only; source legal audit3850 named texts/731 unique hashes. Exact native
package notice retention remains a gate. make check264 passed.

### Rust stage reconciliation and actual tools — 2026-11-08 UTC

Actual x.py install0 after24m29. Collector4 then tried rmdir/etc despite the
legitimate target-spec-json-schema.json. Preserve schema as owned conffile and
already moved completion; no install replay. Guard5 refused the predicted wrong
cause before writes. Probe6 showed Cargo1.97.1, overriding its Cargo.toml fallback
through preceding CFG_RELEASE branch. The earlier source-only fallback inference
was wrong; canonical probe corrected against actual versions/source branch.

Probe7 passed real C/FFI/thread/Cargo unit+doctest, Rustfmt and Clippy positive/
negative checks. Collector stopped only because the native diagnostic normalizes
clippy::eq_op to eq-op; its runner already checked expected exit101. Native8 ran
only the missing Rustdoc0, HTML verified. Derived recovery explicitly preserves
all wrapper failures and per-command exit-file limitation; no passed-test replay.
3704 payload file/symlink entries unchanged,4634 inspected entries,365726903 bytes.
Actual9 ELF dependency sets match existing libc/GCC/LLVM22.1/OpenSSL4/curl/sqlite/
zlib packages. No source version or target security change. Native full-root
b02-rustc-install/PID384579 now performs owned package/legal retention and actual
installed all-tool checks. No owned result accepted until real recipe/post exits.

Host-only Mako1.4.1/Pytest9.1.1 and required build-backend sources authenticated
from frozen book; native Jinja2/MarkupSafe already present, Pytest/Mako absent.
Leaf fetch now permits an explicitly named frozen-parent required/recommended
edge with matching book hash, refusing optional/unrelated/changed/ambiguous
parents; two regressions0, make check266. No Python SDK install or additional
guest writer. No GUI/ISO/physical acceptance.

### B02 owned Rust and proportional serif delivered — 2026-11-08 UTC

Native Rust owned install/post0/0,103.551s with unchanged full-root snapshots;
archive4db0e6bf...3cf63. All nine actual installed tools/FFI/thread/doctest/
positive-negative checks passed. Complete3850 named legal texts retained. Raw61
member evidence bundle791894 bytes SHA760e2b6af530c7de4c13ad7f9d16c9d229790fbcc4c677f4f3acae47f1829340
retained for final release; no release artifact/ISO availability claim. Preserve
all failed collectors, successful compiler/std evidence and archives; no rebuild.

DejaVuSerif four original faces isolated0, owned install/post0/0. Real native
family/weight/slant/Portuguese/Cyrillic and FreeType i/W advances passed; generic
serif now DejaVu Serif, Sans/Mono remain Adwaita. Pango serif-fonts8 actual0,17
affected drivers with original binaries unchanged;11 font SHA inputs retained.
Unrelated core/metric cases reused and original golden failure preserved. No
graphical GNOME/browser acceptance. Next native Mako/keyboard/graphics prerequisites,
Pytest/backends host source cache only, one guest writer remains required.

### B02 native Mako and scoped test-tool source closure — 2026-11-08 UTC

Mako1.4.1 first copy failed before wheel: one public archive doc was0600/root
owned. Verify archive and extracted contentSHA a5620499...1e31, normalize only
that file0644 with explicit operation/prepared receipt; all bytes/version intact.
Preserve partial source and original failure. Resume2 native0, wheel and six real
Unicode/escape/loop/inheritance-cache/syntax-rejection/C-codegen consumers asUID101.
Owned install/post0/0, same six installed consumers, original MIT/AUTHORS retained.
No full pytest or GUI acceptance. Source helper records the normalization for
fresh builds rather than weakening compiler isolation or global permissions.

Pytest's frozen backend closure is source-prepared only. Existing native
packaging26.3/Setuptools84/flit_core are reused; no foundation upgrade. Poetry-core
2.4.1/Pathspec1.1.1/Tomlkit0.15.1/Trove-Classifiers2026.6.1.19 source pinned from
required frozen leaf links. Trove's actual pyproject also requires Calver absent
from its book paragraph: official PyPI2025.10.20 source SHA c98b376c...835f5 frozen,
not a product runtime dependency. Its documented SOURCE_DATE_EPOCH control must
preserve Trove's2026.6.1.19 calendar version when building later; do not silently
produce a current-date package. Native test-tool build/qualification remains next.

### B02 native Python test-tool closure — 2026-11-08 UTC

Twelve independent source-authenticated wheels/stages0 under existing UID101/
caps0/offline/RO-input isolation. Exact frozen wheel metadata, including Calver
2025.10.20/Trove2026.6.1.19 under fixed SOURCE_DATE_EPOCH, verified before private
installation. Actual dependency closure, TOML comments, C lexer and Pytest native
fixture/parameterized pass2 + deliberate fail1/JUnit results passed. No full
upstream-suite claim. Controlled per-package owned archives and installed checks
recipe/post0/0, one34.93s full-root slice; existing foundation modules unchanged.
Complete named notices include Poetry-core vendors; all package archives/index
SHAs and raw evidence retained. Three wrong-package/version/ambiguous-wheel guards
and make check269 passed. Next keyboard data/libxkbcommon pair, not old SDK suites.


### B02 native keyboard and headless validation SDK — 2026-11-08 UTC

Pinned keyboard data2.48/libxkbcommon1.13.2 with exact required book patch built
in qualified UID101/offline/RO-input isolation. Original library26 drivers passed;
data failed because upstream invokes missing xkbcomp and reached60s timeout.
Preserved failure and compiled/staged outputs. Built selected ten-source headless
Xorg SDK including xkbcomp1.5.0, independent stages/archives. libXau1/libXdmcp1/
libxcb check-pc1/libX11 Compose1 passed; optional Check units0registered and
xorgproto libevdev verification upstream SKIP explicit. C API consumer0; original
empty compatibility-map fixture failed after API success, corrected compiler-only
recovery2 valid0/invalid1 with stages unchanged. SDK owned recipe/post0/0 in38.552s.

Original keyboard data rerun with real comparator:5516PASS/3164optional pycountry
ISO-country/language SKIP in14.72s. New locale/Compose affected library2rechecks0;
411 original library ELF hashes and both stages unchanged. Actual US/BR/PT Shift
and registry consumer0, owned pair recipe/post0/0 in29.409s, installed frozen
versions/default data root verified. Raw failures/tests/archives/notice inventories
retained. No native GNOME, physical input, installer or G2 acceptance inferred.
Grouped-book exact-archive guard adds two regressions; make check271passed.
Next selected graphics/render prerequisites for actual GTK/GNOME session.


### B02 native render prerequisites and scratch custody — 2026-11-08 UTC

Libpciaccess0.19 unknown-ID/cleanup consumer0 and owned install/post0/0 (27.452s).
No upstream executable suite is registered. Original build1 completed/staged but
fixture was misnamed.py; exact bytes renamed.c with explicit receipt, host helper
now derives suffix from selected probe. Consumer-only resume2 passed, three stage
files unchanged; no rebuild. Libdrm2.4.134 with Intel/Radeon/AMDGPU/Nouveau/vmwgfx
libraries passed13 registered tests; drmdevice/threaded upstream SKIP77 without
devices. Native hash/format/modifier/invalid-FD checks0 and owned install/post0/0
(49.708s). This does not qualify a GPU, window or display.

PyYAML6.0.3 pure-Python build tool passed1283 original fixtures and native Unicode/
anchor/invalid-YAML/unsafe-constructor-refusal consumers; optional LibYAML C
accelerator explicitly absent. The upstream main ignores its boolean result;
asserted real boolean plus nonempty/error-free count. Owned install/post0/0 in
53.343s. Full notices and raw native/failure/recovery evidence retained.

ADR0131 verified both duplicate GCC metadata stages against all1975 canonical
payload entries and retained archiveSHA before guarded retirement. Reclaimed
3,821,027,328B; target free23,630,069,760B. Installed compiler/source/compiled tests/
recovery/backings untouched. Receipt/sentinels prevent uncertain replay. No compiler
suite rerun. Mesa26.1.7 first reference Wayland/software render source authenticated
and isolated mesa-1 started; tests, stage, native EGL/GLES pixel proof and owned
installation pending (ADR0132). No native GNOME/Phase2ISO/G2 acceptance claimed.


### B02 owned native Wayland software rendering — 2026-11-08 UTC

Mesa26.1.7 reference EGL/GBM/GLES/llvmpipe/softpipe/virgl/svga profile compiled.
Original43/48 upstream drivers passed; five Python wrappers lacked two executable
build_by_default:false test dependencies omitted by --no-rebuild. Resume2 built
only those tools and rechecked5/5, original1266 ELF hashes unchanged. First stage0;
consumer link then needed indirect libgallium/gbm search. Consumer-only finish3
uses link-time rpath-link/no runtimeRPATH; complete stage and original ELFs unchanged.
Original job1/job2 failures remain1, final3actual0. No source/test assertion edits,
no core rebuild or passed-suite replay. Fresh recipe declares missing tools/path.

Staged and owned installed actual EGL1.5/GLES shader compilation, triangle draw
and pixel readback0,32,64,255 via llvmpipe LLVM22.1.8. Native install/post0/0 in
77.302s; archive169289ff...48f121,6876 named/header notices retained, real dynamic
ABI audit recorded. EGL/GLES/GBM pkg-config versions use source project26.1.7,
not EGL API1.5. Epoxy1.5.10 EGL-only native4 portable upstream tests0 plus actual
staged/installed Epoxy dispatch/version/shader/raster/pixel0; owned0/0 in48.281s,
42 notices. X11-dependent upstream contexts unregistered, independent real
surfaceless consumer required. Raw failures/tests/pixels/package proof bundles
retained. No GNOME/window, physical GPU, GLX/Vulkan or Phase2ISO/G2 acceptance.
Next native GdkPixbuf2.44.7 PNG/JPEG/GI and frozen librsvg/GTK prerequisites.


### B02 native image primitives and frozen Rust sources — 2026-11-08 UTC

GdkPixbuf2.44.7 PNG/JPEG/GIF builtin/GI profile passed23 registered upstream tests,
actual PNG/JPEG stream roundtrip, malformed-image refusal and format registry.
Upstream suppresses global loader-cache updates under DESTDIR: retained actual
native generated comments-only external-loader cache, asserted no temporary paths
and owned it. Native install/post0/0 in55.229s plus actual Python GI PNG/pixel0 and
cache hash. SVG and optional loader profiles remain unqualified; no GTK window.

Cargo-c0.10.24 GitHub source omits Cargo.lock. Authenticated official published
crate0.10.24+cargo-0.98.0 lock supplement: same VCS/tagd7d174...7b27, exact original
Cargo.toml and12 published Rust files; source/version unchanged. API route403
replaced by official sparse registry checksum, no retry/auth workaround. Reused
cached official1.96 seeds privately for source-only Cargo vendor; no host install/
source compilation, native product SDK1.97.1 unchanged. Both parent sources frozen:
418 cargo-c and352 librsvg registry crates, full package/file checksums verified,
unchanged locks, deterministic vendor archives and per-crate licenses. Three input/
cache refusal guards passed. Source acquisition is not native build acceptance.

Native cargo-c1 stopped before compilation: six public fnv1.0.7 files extracted
root-owned0640 deny UID101 checksum reads. All vendor hashes verified, only six
modes0640→0644 with exact byte preservation/receipts, initial101/wrapper1 logs kept.
Future preparer normalizes verified public readability. One regression confirms
bytes/private sibling unchanged. Unique native resume2 reuses exact source/config
and cached metadata; no privilege/source/version change or passed-suite replay.
Native cargo-c/librsvg/SVG/GTK and complete desktop acceptance remain pending.


### B02 native cargo-c qualification

[Native build and probe recovery](evidence/B02-cargo-c-build.json) preserve the original
public-source readability failure101 and unaccepted version-help probe. Same-byte
six-file mode correction yielded native build0/upstream25PASS/0ignored. Direct
plugin version correction qualified11 actual checks, Rust fixture1PASS and C ABI
header/pkg-config/shared+static consumers returning42. Four stage binaries unchanged;
no successful source/compiler suite replay. [Owned installation](evidence/B02-cargo-c-install.json)
recipe/post0/0 in110.292s and installed offline C ABI checks0;9143 legal notices.
Build-only tool, no base/live/catalog availability implied. Raw53-member evidence
SHA68f4e20df4751d24b3108fdbdbdc22be2996b586138dcc9a9c18c87d1996b2d9
retained for release. Native librsvg/SVG/GTK/desktop acceptance remains pending.


### B02 native SVG/TIFF and source custody

[SVG build/qualification](evidence/B02-librsvg-build.json) retains the original upstream
result:1364 Rust cases passed, one text-decoration golden failed, plus four of
five registered drivers passed. [ADR0134](adr/0134-svg-pango-decoration-reference.md)
records the selected Pango1.58.2 source/independent geometry oracle: exactly12
strike endpoint pixels, no other image changes. No golden replacement/tolerance
change or144 existing ELF rebuild. Stage and actual SVG/Cairo color, malformed
input refusal and Gdk SVG loader consumers passed.

[Owned renderer/cache](evidence/B02-librsvg-install.json) recipe/post0/0 in107.717s,
actual installed C and GI SVG+PNG pixel roundtrip0,6849 legal notices. The Gdk
2.44.7-1+toddy2 transaction changes only its owned generated loader cache; other
446 original package payload entries unchanged. SVG archive
8ea71609cd4cd23b56e43b9a90695640ad134e10af68575e592178098961ca15;
raw72-member evidence bundle SHA7d204cc54e87029d4610ab6c655f13319230dd881c446dd51756dc795b2d3828.
Original golden remains failed; no window/GNOME/physical GPU acceptance inferred.

[TIFF4.7.2 native156 tests](evidence/B02-tiff-build.json) and
[owned install](evidence/B02-tiff-install.json)0/0 in55.17s, actual LZW/Deflate exact RGB
roundtrip and malformed header refusal with16MiB single-allocation bound.
GTK4.22.4 source directly requires TIFF; the initial Gdk profile still has no TIFF
loader. Archive2c90246f4b5f156cbd0c3ba3903aee8aacce1cd28a3727b35f57922ff37d86ca;
raw16-member evidence SHA30eeb8567db3d60a60885289616daa60e9c3eac88c41af2a37a00fdc77ea8984.

The original iso-codes server twice returned an identical truncated180224-byte
archive. Both copies were quarantined before extraction; the trusted BLFS mirror
returned complete16408049 bytes matching frozen MD5/gzip/SHA256. No version change.
Source qualification does not imply installed locale UI acceptance.

[Host duplicate source custody](evidence/B02-host-source-copy-custody.json) retired only
three byte-for-byte archive-identical expanded source copies, reclaiming1.28GB.
All native compiled tests, source archives, acquisition logs, raw evidence and
private Cargo registry cache retained. No guest/host OS installation changes.


### B02 locale data and GTK bootstrap

[ISO Codes actual data/UTF8](evidence/B02-iso-codes-build.json) verifies16JSON files,
country/language entries, real Portuguese gettext and715 source .po files across
eight nonempty domains. The original Meson bare-domain checker can glob zero
files; those empty checks are not used as UTF8 evidence. Correct only invocation
prefix/cwd of the unchanged source checker. [Owned native data](evidence/B02-iso-codes-install.json)
recipe/post0/0 in60.2s. Raw36-member bundle
SHA51116323c5984f4ee0f671d9e3b305f953fad3f8282d1da7b76a897f9e56eb31 retained.

[Bounded GTK compiler volume](evidence/B02-gtk-build-volume.json) is a private3GiB regular
file inside the disposable builder VM, mounted nosuid,nodev/UID101 at the declared
work path. Host reserve preflight passed; no physical disk/target partition change.
[ADR0135](adr/0135-bounded-guest-compiler-volume.md) records exact UUID/backing/
recovery guards. [ADR0136](adr/0136-gtk-wayland-bootstrap-profile.md) separates
Wayland bootstrap/headless API checks from actual GNOME/window/media acceptance.
Native GTK build is running; no graphical criteria are marked completed.


### B02 native GTK bootstrap installed

[GTK source/API/GI qualification](evidence/B02-gtk-build.json) passed30 original headless
cases (15bitset/10stringlist/5RGBA), actual C and Gtk/Gdk/Gsk GI consumers and strict
staged schema cache. [Owned native bootstrap](evidence/B02-gtk-install.json) installed0;
original postcheck1 preserved because it queried a GTK3 schema name. Actual frozen
GTK4/current registry uses org.gtk.gtk4.Settings.FileChooser. Read-only full
installed payload/archive verification and corrected postcheck-only recovery0/0;
no reinstall/library build or upstream test replay. Native installed API/GI/schema
checks0,2132 retained legal notices. Archive
71926defa7412777f080e97a4ad41ed49b328b272008caa5ddb3d9c8592c3b00.
Raw28-member bundle SHAaac6fa6b87abe79fcc618dfe2e1f9adbe51baacdc0832cb1736f7142a09ef2dd
retained. This is not an opened window, GNOME session or media qualification.
Theme/schema/AppStream/Libadwaita/service integration and actual UI QA remain next.


### B02 native resource/cache integration

[Resource qualification](evidence/B02-desktop-resources-build.json) stages Hicolor0.18,
Adwaita icons50 and GSettings schemas50.1 independently. No executable upstream
suites are registered; zero is not a pass count. Both real icon caches validate.
Original probe1 requested a property unavailable on a plain C enum; frozen header
ZOOM=5 and probe-only recovery2actual0, all938stage files/links unchanged.

[Owned native resources](evidence/B02-desktop-resources-install.json) and GTK4.22.4-1+toddy2
schema/legal-only cache upgrade installed/post0/0 in70.624s. Compare complete
installed schema inputs to the qualified private union first; other GTK runtime
payload entries unchanged, no library rebuild/user preference writes. Actual
native52schemas, default Adwaita Sans/Mono fonts, GI enum, two named icons,
32x32 SVG-to-PNG and Xcursor data checks0. [ADR0137](adr/0137-native-desktop-resource-transactions.md)
records ownership/recovery and the bounded512MiB compiler volume.
Raw94-member bundle SHA29f5f3b9e027f065e9213014760bf1a0bc11419e71c81672aab0ebf46db6975f
retained. No graphical GNOME/window/pointer interaction acceptance follows.

Next: native AppStream1.1.6 required by actual Libadwaita source. Its data build
needs itstool and therefore the optional Python binding of the already owned
libxml2-2.15.3; preserve the core library/tests and frozen version. Authenticated
libxmlb0.3.29/libfyaml0.9.6/libxslt1.1.45/itstool2.0.7 sources are cached. Select
actual bootstrap requirements from source; source qualification alone does not
make packages/catalog candidates available.


### B02 verified native vendor source custody


[Native expanded-vendor custody](evidence/B02-native-vendor-source-custody.json) retired only
two archive-identical public input copies after accepted cargo-c/librsvg package
and archive verification. Compared27,238+19,348 file entries, reclaimed872,890,368B;
target free17,240,117,248→18,113,007,616B. Source archives, locks/prepared receipts,
compiled binaries/tests, native packages and raw evidence remain. Restore only
from frozen archives if a changed Rust slice needs them; never repeat acquisition,
retirement or an accepted build. This preserves the16GiB target reserve for the
next native dependencies.

Frozen libxml2's Python Meson generator explicitly requires Doxygen even when API
HTML installation is disabled. Doxygen1.18.0 source is authenticated/cached; build
it before the optional binding. This adds a concrete generator dependency, not a
core XML rebuild, mandatory desktop application or catalog availability claim.
