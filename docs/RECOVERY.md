# Development recovery

Current stage: H07 final base, after accepted GCC suites and native compiler installation. H06 /tools removal and actual paired-disk restoration passed. Target root is /dev/vdb4 mounted at /mnt/lfs.
No ISO exists. Gate G1 and G2 remain pending. Inspect status.json and actual
processes before continuing; this document is updated at verified boundaries.

## VM lifecycle

```sh
python3 scripts/host/vm.py inspect
python3 scripts/host/vm.py ssh 'hostname; lsblk -o NAME,SIZE,SERIAL,MOUNTPOINTS'
python3 scripts/host/check_requirements.py
```

Container: toddy-builder. SSH: loopback port 2222. Private identity and
known_hosts: .local/vm/; never commit or include these in an image.
Serial log: .local/vm/serial.log (replaced on restart).

Use python3 scripts/host/vm.py stop for a clean shutdown; it waits for QEMU to
exit and removes the stopped container. Use start to resume. If a container
has already exited, inspect docker logs and its exit status before removing
only that container. Do not remove disk files or recreate a working target.

An offline copy of the configured builder is at
.local/vm/checkpoints/h01-builder.qcow2. Its backing image is
.local/vm/builder-base.img, exposed at /vm/builder-base.img inside QEMU's
container. Restore the copy only while the guest is stopped; preserve the
failed overlay first. H03 adds a paired builder/target checkpoint.
The checkpoint is a convenience on the same disk, not disaster recovery.

Historical H03 paired checkpoint: .local/vm/checkpoints/h03-builder.qcow2 and
h03-target.qcow2. Restore both together with QEMU stopped, preserving the failed
disks first. The H01 checkpoint predates target preparation.

## Current verified checkpoint and next action

Latest verified cold pair: .local/vm/checkpoints/h07-native-services.json with
86 accepted native packages through Curl. Both copy hashes and qemu image
checks passed; .local/logs/h07-native-services-checkpoint.exit is 0. Builder
SHA-256 04f0d30eaf79e029948feae68255b20c3cab9a79dd4d67756af5128d6de44519;
target SHA-256 536109a5db3f6f2c44620c33f954fc2ce96570636c9a6b33bbc1b708e57785fd.
This pair was saved/verified, not yet restored. H06 restoration was actually
exercised. Copies share the workstation disk and are not disaster recovery.

Groff/Kbd/Tar/Systemd/E2fsprogs recoveries passed. Keep qualified raw failures
and H12 native namespace obligations (ADR-0023/0025/0027). Do not infer all
upstream tests passed from dispatcher recipe/postcheck zero. Live system now has 101 accepted native packages through native Dpkg.
Full Vim PTY/SHELL retry passed 8014 executed/200 skipped/zero failed and every
planned result file. Current continuation: h07-package-manager-driver.sh.
Inspect actual h07-dpkg/h07-berkeley-db records and driver exit before dispatch.
Initial Dpkg safe extraction refused three official FIFO fixtures before any
installed changes. Partial tree/failure retained under sources/recovery and
build/history/dpkg-extraction. Exact archive/name/type allowance added with
standard path/mode/ownership checks; full retry and native Dpkg postcheck passed.
Berkeley DB standard attempt was stopped after a reproduced test142 fixture
isolation failure; C tests had passed, no production install occurred. Test-only
DBM/compat185 and static object generation satisfy actual upstream test/symbol
requirements; production still omits DBM/compat185 and stages no .a/.la files.
Inspect /sources/db-5.3.28/build-test/ALL.OUT for live progress, not only tee tail.
Prepared native Perl/Triehash/Which/Libseccomp/APT recipes are not yet accepted.
Once dispatcher is quiescent, sync then run h07-perl-test-tools-driver.sh; it
uses accepted native Dpkg backend and must pass real package postconditions. Native APT, full packaging-backend integration and ownership/dependency/conffile/license
closure remain pending. The archive-only native backend probe passed without
changing the main database (ADR-0035).

After an offline restore/restart:

```sh
python3 scripts/host/vm.py start
python3 scripts/host/vm.py ssh 'bash /opt/toddy-build/scripts/build/mount-kernfs.sh'
python3 scripts/host/sync_build.py
python3 scripts/host/vm.py ssh 'nohup bash /opt/toddy-build/scripts/build/h07-supplemental-tools-driver.sh > /var/log/toddy/h07-supplemental-tools-driver.log 2>&1 < /dev/null & echo $!'
```

Old supplemental orchestration was deliberately stopped only after Curl's
success marker and absence of running dispatchers. The boundary record is
/var/log/toddy/h07-supplemental-boundary-pause.json. Its enclosing E2fsprogs
driver may record 137 for the stopped shell; this is not a package/test failure.
Do not resume the old stopped PID. Fresh driver skips accepted packages, then
runs remaining native support and signing libraries. Vim requires the guarded
h07-vim-glvs-inputs success before any downloader test. The prepared step checks
protected cache/archive paths and actual unprivileged HTTPS downloads of the
four frozen versions (ADR-0028). Preserve failed preflight logs before retry;
never expose unverified code or delete upstream tests.

Full sync must hold the exclusive guest lock and refuses active recipes. An
input-sync.running flag means interrupted installation; inspect/preserve staging
and finish verified sync before dispatch. After a guest restart mount kernfs
first. Never run a pristine-source resumer on an installed/compiled package.
H08 must replace temporary build resolver 10.0.2.3 and generate proper per-machine
identity; H12 must rerun Systemd namespace and Glibc container-dependent tests.

Never rerun account bootstrap or re-extract successful build trees. The GCC
suite marker proves compilation/tests only; installation is separately proved
by h07-gcc-install-recovery.success.json. Ncurses is separately proved by
h07-ncurses-recovery.success.json. The first installation attempts changed
zero installed paths. Fresh builds use corrected original recipes; explicit
resume scripts only apply to those recorded failures and existing stages.
Older continuation notes below are historical, not current job instructions.

## Storage and resource boundaries

Only .local/vm/lfs-target.qcow2 is the disposable OS build disk. In the guest
its serial must be TODDY-LFS-TARGET. The root disk has TODDY-BUILDER serial.
Never pass workstation block devices into QEMU. Retain 100 GiB host reserve,
begin with 8 compiler jobs, and stop on memory/disk pressure. Before any disk
operation verify hostname, virtualization, serial, capacity and mounts.

H12 obligation before G1: rerun Glibc container-backed UNSUPPORTED cases in the native booted target; current chroot cannot create nested user namespaces (unshare(2)). Preserve original raw reports and compare actual new outcomes.


Latest verified partial-H07 checkpoint: h07-early-base (paired disks and JSON
manifest under .local/vm/checkpoints). Thirteen native packages passed through
PCRE2, with retained logs. The current next/running driver is
/var/log/toddy/h07-test-tools-driver.pid and .log/.exit, covering M4, Bc, Flex
and Tcl. Inspect actual PID and per-package records before retry. After a VM
restart, mount-kernfs.sh must run before chroot. Final compiler/binutils suites,
remaining base packages, native package-manager build, dependency/ownership
closure and the H12 native container-test rerun are still pending.

2026-11-06 continuation: M4's signal-environment failure is corrected and its
full retry passed; Bc and Flex also passed. Inspect the test-tools driver and
h07-tcl records before resuming. The runner resets inherited ignored signals
before every recipe/postcheck. Recovery source tree
/mnt/lfs/sources/recovery-m4-inherited-signal preserves the original failure.
The prepared h07-harness-driver must start only after Tcl passes; Binutils
build/test is separate from installation so critical results can be classified
before changing the live target. No critical suite is skipped.

Current continuation: all test-tools and four harness packages passed; the
h07-harness-driver now runs h07-binutils-build (build and mandatory suite
only, no installation). Check /var/log/toddy/build/h07-binutils-build.* and
/mnt/lfs/sources/evidence/h07-binutils/check.exit, check.log and
test-reports.tar.gz. A nonzero test exit must be classified from raw reports
before a separate installation step. Latest cold checkpoint remains
h07-early-base, preceding these eight native packages. Current target has 21
packages. Tcl optional client limitations are in ADR-0011; no new credentials
or service is needed to continue the core book build.

Latest verified cold pair: .local/vm/checkpoints/h07-native-math.json and its
two qcow2 files. Contains 25 native packages, accepted final Binutils plus
GMP/MPFR/MPC. The original Binutils build record remains failed with raw suite
exit 2, while classification accepts only the exact source-documented
profiler failure; separate binutils-install passed. Do not rebuild it merely
to turn that original raw exit into zero. GMP's first result-format assertion
failure also remains preserved; explicit gmp-install resumed and passed.
Current job: /var/log/toddy/h07-permissions-driver.{pid,log,exit}, Attr then
ACL. Inspect package records and exact test outputs before retry. Next in
book order: Libcap, Libxcrypt, Shadow, Gawk, then final GCC critical suite.

2026-11-06 latest running job: h07-accounts-driver invokes h07-gcc-build after
verified Shadow/Gawk. /var/log/toddy/build/h07-gcc-build.{log,running.json}
holds PID/PGID and build output. After compilation, the complete unprivileged
critical suite writes /mnt/lfs/sources/evidence/h07-gcc/check.log, check.exit,
test-summary.txt and test-reports.tar.gz. Inspect terminal records; a running
PID/marker is unfinished. Do not execute test-summary.txt: upstream's report
is a printed shell mail script, retained as data only. Never send it.
Classify every unexpected outcome before separate final GCC installation.
The original Shadow postcheck failure remains preserved; shadow-audit passed
without reinstalling. Native target has 31 packages, latest cold checkpoint
h07-native-math predates the six permissions/accounts additions. H08 must
supply /run/dbus creation at native boot; test ACL copies after final Coreutils.

Before final H07 closure, repair the direct dependency declarations found by
actual ELF audit: Bc/Readline, Binutils/Flex, Gawk/Readline and Shadow/ACL, plus
the C++/terminal providers once final gcc-runtime/Ncurses are installed. Use
versioned native metadata updates with original archives retained. Re-run
scripts/build/audit_native_elf.py inside the guest; its partial report does not
cover optional dlopen, tools/data/plugins or dependency version constraints.

GCC suite finished and independent classification accepted all six reports:
511240 PASS, only 72 known FAIL/two known XPASS, no unknown outcomes. The raw
suite exit is 0. Complete merged/parallel reports and original recipe sidecar
are copied to .local/logs/h07-gcc. The VM is being stopped for the paired
h07-gcc-tested checkpoint before installation; verify the host checkpoint
manifest/log before starting. Then start VM, mount-kernfs.sh, and run a guarded
h07-gcc-install step with its prepared postcheck. Never infer installed GCC
from h07-gcc-build.success.json: the build changed zero installed paths.


Additional recovery ingredients (not a replacement for the verified cold pair):
.local/native-package-snapshots/20261106T053457533866Z contains 47 native archives,
full metadata and hash-verified inventory/verified.json. Recreate this cache at
new verified boundaries with python3 scripts/host/collect_native_packages.py.
It copies only installed project-built packages, never signing/provider keys.
A partial destination without verified.json is not an accepted cache. The
snapshot predates Perl. H07 rehydration from these archives has not yet been
exercised; do not describe it as a tested system restore.


Prepared H07 closure (not executed while BDB suite holds lock):
linux-api-headers, filesystem-layout, lfs-build-support, native-bootstrap-cleanup,
native-metadata-closure recipes/postchecks. Metadata upgrade preserves original
archives and records, records per-package progress under sources/evidence/
h07-metadata-closure and skips only independently verified completed versions.
An existing staging directory or leftover package transfer is a diagnosis point,
not permission to delete it blindly. Native backend/notice retention is prepared
in the checkout but not yet synced to the running target. After quiescent full
input sync, the next Perl/Triehash support recipe must prove real native Dpkg
routing; inspect its packaging_backend metadata and native postcheck.


Next prepared driver chain after actual BDB result (do not dispatch concurrently):
1. Inspect h07-berkeley-db success/failed/running and the package-manager driver
   exit. Active standard suite logs are /sources/db-5.3.28/build-test/ALL.OUT;
   partial progress without Regression Tests Succeeded is unfinished work.
2. When no dispatcher remains, run full verified input sync. The checkout now
   includes native Dpkg routing, ownership policy, complete notice retention,
   CPAN/Triehash/Which/Libseccomp/Tcsh sources/recipes and interpreter audits;
   none of those new inputs has been synced while BDB is active.
3. Run h07-perl-test-tools-driver.sh and inspect every native marker/postcheck.
4. Its success permits h07-final-base-driver.sh: APT real signed repository,
   Python-owned command alias metadata, full ACL retest, API/layout ownership,
   exact bootstrap quarantine and versioned metadata closure. Stop on actual
   failures for diagnosis; prepared code/driver exit alone is not acceptance.
The Python-only upgrade preserves old archive/record and writes per-package
progress under h07-metadata-closure/packages. Full closure reuses that verified
version, derives actual ELF/interpreter edges and requires zero unqualified
findings plus native package-manager checks. Additional tool/data/dlopen, image
credential/source/license and native-kernel obligations still remain before G1.


Additional 101-package recovery cache (not a cold image or tested restoration):
.local/native-package-snapshots/20261106T104331341467Z, inventory SHA-256
00b1e1f3709eef2c19ad0b55c5b39b14cb1d6a93514ab9ce2344686306890380,
archive SHA-256 fcc82a8eb9abc23fe59c9000151fbce2686a79f1c1ace365729f6483eebf7f29.
The current accepted boundary remains 101 while BDB is active. Native build-flow,
XML consumer/bounds and package-backend archive-only reports under .local/logs
are supplemental probes, not new installed packages or completed H07 evidence.


Prepared H08 is not the next dispatch while H07 remains incomplete. Its guard
requires synchronized H07 completed/H08 in_progress and actual final native
closure success. It preserves only the four hash-pinned unowned bootstrap
configs under /sources/recovery/h08-bootstrap-config-*/ before installing native
configuration; changed/owned/redirected inputs refuse before deletion. Backup
files and manifest/directories are fsynced. If installation fails, inspect native
Dpkg ownership/status and preserved manifest before restoring anything; do not
copy bootstrap files over package-owned conffiles blindly. Prefer the next
verified H07 cold pair for whole-target rollback. Timezone/resolver links are
mutable generated state; /run chroot resolver bytes must never enter an image.
No H08 target mutation or boot/network acceptance has occurred. See ADR-0042.


Latest H07 continuation supersedes the old BDB-running notes above: test142
failure is reproduced; failed marker records recipe -15/postcheck null/zero
installed changes. History is /var/log/toddy/build/history/
berkeley-db-test142-20261106T161146Z. The compiled test tree remains available;
do not delete it or manufacture a BDB success marker. At quiescent input sync,
run independent h07-perl-test-tools-driver.sh. Correct the fixture with all
assertions retained, capture focused test exits, then rerun the complete BDB
standard suite before production install/acceptance and APT. No H08 target step
is eligible until complete H07 acceptance. First new package must prove actual
source-built native Dpkg routing in its archive record and installed postcheck.


Updated continuation after native support progress: 16 CPAN modules accepted;
117 accepted packages total, 118 installed including Triehash whose old postcheck
fixture used stdin instead of its documented filename argument. Native corrected
CLI/C lookup check passed; run h07-triehash recovery with triehash-recovery.sh and
corrected triehash-check.sh under the same step ID, then resume the support driver
for Which/Libseccomp/Tcsh. Perl shared-journal ownership correction is accepted
through preserved-archive Tagset +toddy1; no live perllocal.pod remains.

BDB patch is frozen in supplemental inputs (151 total inputs). Native focused
plain/range/callback correction cases captured exit 0; full suite still pending.
Root-protected cached test-build seed is /var/log/toddy/build/
h07-berkeley-db.recovery-seed.json, 460 verified files, SHA-256
75d8c0e77db2c0b42af7de2ff813e908ee4f2d5cc470dcb62bb5082013937e63;
host copy .local/logs/h07-bdb-build-recovery-seed.json. After support jobs finish,
sync committed inputs and dispatch the same h07-berkeley-db step with
h07/berkeley-db-recovery.sh and h07/berkeley-db-check.sh. It archives old TESTDIR/
logs, verifies frozen source/build hashes, applies the exact fixture patch,
repeats C/focused tests and the complete standard suite before production install.
Do not mark BDB accepted from the focused result or reuse the failed partial log.


121-package verified native cache: .local/native-package-snapshots/
20261106T165051482536Z, inventory SHA-256
28179c27a71eebb3360e61b89321bc91de0cc7acd842398513aaae5e8760316d,
archive SHA-256
0144fa27d9c5ceb5daca0ba07c109a20148f97f7c90ec3d588b6e0b853048f38.
This is not a bootable checkpoint or demonstrated restoration. The independent
ownership driver's initial prerequisite refusal made no target changes; use
its corrected final-Coreutils original/recovery success-marker handling.


124-package verified cache: .local/native-package-snapshots/
20261106T170238245622Z, inventory SHA-256
6ffae48dab7722834cb29e01c1607ea4cb62346c21ce4dd36f3ab97435583a85,
archive SHA-256
0a39ab5a88ea8c950b0f58a9577b3c63533615b9769516109dcc0de330609eed.
Independent ownership driver exit 0; lfs-build-support 13.1-2 native correction
accepted with original 13.1-1 failure/archive preserved. Cold pair is being
saved separately; this package cache itself is not a bootable checkpoint.


Newest verified cold pair is now h07-native-support (124 accepted packages),
created 2026-11-06T17:03:54Z. Save exit 0; both source qcow2 checks and copied
SHA-256 checks passed. Manifest .local/vm/checkpoints/h07-native-support.json;
builder SHA-256
15ae02e094dc1703a94e5ff88df2c37bff1d6888b9c9a25a58103ea9d54470fd,
target SHA-256
6ab9dfda166f0d01bc48c247cec0a9c0c3613fc138125b61d2f85a64c1a5eaf1.
Raw save log/exit: .local/logs/h07-native-support-checkpoint.{log,exit}.
Not restored in this run; earlier H06 controlled restoration remains the
demonstrated restore. This pair includes the BDB compiled-test recovery seed,
old failures and corrected native support; it contains no accepted BDB/APT.

Resume after normal builder start and mount-kernfs.sh, verify/sync committed
inputs while quiescent, then run_step.py h07-berkeley-db
h07/berkeley-db-recovery.sh h07/berkeley-db-check.sh --user root from
/opt/toddy-build/scripts/build inside the builder. The same-step retry must
verify the 460-file seed and all 483 Tcl files after applying the correction
before full standard execution. Keep PID/log/exit; only 0/0 accepts installation.


Corrected BDB retry now runs inside the restarted builder: launcher PID 1364,
runner PID 1365; durable driver prefix /var/log/toddy/
h07-bdb-corrected-standard-driver (log/pid/exit). Actual build log
/var/log/toddy/build/h07-berkeley-db.log; standard log
/mnt/lfs/sources/db-5.3.28/build-test/ALL.OUT. C tests and all three focused
regressions passed; full standard suite started 2026-11-06 17:12 UTC and is
unfinished. Do not run full sync or another dispatcher while it owns the lock.
Original partial suite state preserved under history/
berkeley-db-before-corrected-suite-20261106T170904Z.

Latest checkout also prepares canonical Perl packlist upgrades (ADR-0045).
They are NOT installed in the current builder. After BDB reaches a durable
success/failed result and no recipe remains active, sync current committed
inputs before h07-final-base-driver.sh. It retains mandatory BDB/APT gates and
will require zero native packlist findings and exact version/policy evidence.


Additional source preparation during the active DB suite: ADR-0047 freezes
four future image-tool archives (155 total selected inputs) in the checkout
and host cache only. Native bsdcpio newc private roundtrip passed; no GNU cpio
component was added, no H10 image exists. Do not sync until BDB's dispatcher
finishes. H09/H10/H11 remain unstarted; native boot/overlay/ISO gates still apply.


Additional H11 preparation: python_qa.py stages an optional regression-data
partition only after the H10/H11 status gate. Its private own-archive experiment
passed; no runtime/QA package transfer has run and H07 counts remain unchanged.
Public upstream test-key fixtures must be separated from default release roots
and on-medium runtime repositories through real Dpkg ownership transfer, with
complete QA retained outside the image. See ADR-0049 and the scoped raw audit.


H09 direct-root GRUB renderer is source preparation only. It writes stdout,
requires measured filesystem/GPT UUID arguments, and has not changed /boot or
the ESP/MBR. Native syntax probe passed in a removed private temporary file;
see ADR-0046. Actual installation still requires the H09 gate, accepted native
kernel and repeated designated disk/partition/mount identity guards.


## H07 success-gated continuation supervisor

Session-local .local/scripts/h07-after-bdb.py is armed with durable log
.local/logs/h07-after-bdb.log and atomic state
.local/logs/h07-after-bdb.state.json. It waits without repeatedly fetching
unchanged test output. It requires the complete DB driver exit 0, actual
recipe/postcheck 0/0 and no running recipe, then requires a clean checkout,
records the selected commit and performs full exclusive input synchronization.
Only then does it launch h07-final-base-driver.sh in the guest with its durable
log/PID/exit files. It waits for that result and verifies all final markers.
Any failure stops for diagnosis; it does not retry an unchanged failure or
mark H07 complete. Evidence review and the final cold checkpoint still precede
acceptance. No input transfer occurs while Berkeley DB owns the build lock.

Before resuming, inspect that local state, actual guest processes and final
markers; do not launch a duplicate dispatcher. The supervisor uses a local
exclusive lock. If interrupted while waiting, inspect results first and resume
from the exact verified boundary; do not rerun completed builds. Guest final
driver logging remains /var/log/toddy/h07-final-base-driver.log and .exit.


The final-base driver now records its PID and installs the exit-status trap
before prerequisite checks, matching the independent ownership driver's
convention. A missing prerequisite produces an explicit diagnostic and exit
file instead of leaving the supervisor with an absent result. Syntax and all
97 local checks pass; actual final dispatch remains pending behind DB success.
This prepared correction is included at the next quiescent input sync.


H09 prepared order after H08 acceptance/status synchronization: run the
kernel recipe/postcheck, then h09-boot-config with h09/boot-config.sh and
h09/boot-config-check.sh, then h09-bootloader with h09/bootloader.sh and
h09/bootloader-check.sh through run_step.py --user root. Preserve a verified
cold paired VM checkpoint before the bootloader step. The recipe is initial
installation only and refuses existing output/evidence; inspect partial
results rather than deleting them to force a rerun. Before-sector snapshots
and partition dumps are under /sources/evidence/h09-bootloader in the target,
excluded from release images/Git. Prefer restoring the verified disposable
cold pair for a failed boot-track experiment; sector backups alone are not a
complete system checkpoint. Actual BIOS/UEFI early boot remains a separate
mandatory acceptance step after artifact checks. No H09 dispatch has run yet.


Mtools 4.0.50 is frozen as an additional H11 GRUB EFI image dependency in
ADR-0050. The source cache and detached-signature evidence are outside Git;
scripts/fetch_security_overlay.py --supplemental reproduces SHA verification.
Do not sync it into the builder while the DB recipe owns the build lock.
Native build, exact GRUB FAT-image roundtrip and actual ISO UEFI boot are still
pending. The upstream check target contains no self tests; it cannot replace
those checks. Existing H07 124/126 package counts exclude this future tool.


After H10 acceptance and synchronized H11 in_progress status, Mtools can be
run through run_step.py h11-mtools h11/mtools.sh h11/mtools-check.sh --user root.
Its source is already frozen (ADR-0050). Preserve any failed build/staging
before retry. The postcheck uses only a private regular-file FAT image and
removes that fixture after checking real EFI bytes/UTF-8/invalid-input refusal.
Actual ISO assembly and UEFI boot are subsequent requirements. The prepared
H11 gate currently refuses; do not dispatch it during H07.


After H09 acceptance and synchronized H10 in_progress status, run Squashfs
through run_step.py h10-squashfs-tools h10/squashfs-tools.sh
h10/squashfs-tools-check.sh --user root. Native tests use private regular
image files with bounded processors/memory; failures preserve the fixture
path reported in the log. Inspect it before retrying. Actual source build and
all three compressor/metadata/ACL roundtrips remain pending. Passing extraction
checks cannot substitute for the later native-kernel live/overlay boot gate.


After H10 acceptance and H11 status/input synchronization, the prepared ISO
library order is libburn, libisofs, then libisoburn. For each name, invoke
run_step.py h11-NAME h11/NAME.sh h11/NAME-check.sh --user root inside the
builder's /opt/toddy-build/scripts/build directory. Libisoburn additionally
requires both previous success markers. This is separate from the Mtools step;
all four must pass before GRUB hybrid ISO assembly. Do not invoke those recipes
while the H07 database job owns the build lock. No library has been installed
by preparing these files.

Configure logs are under /sources/evidence/h11-NAME. Libisoburn's native ISO
metadata/corruption check preserves failed private /tmp/toddy-iso-roundtrip-*
fixtures, and writes iso-roundtrip.json only after success. Inspect actual exit
and postcheck results, not just image existence. A regular-file roundtrip does
not accept BIOS/UEFI boot, final live root or H11's distributable image audit.


Native boot probe preparation is in scripts/host/boot-probe.py, its .service
and boot-probe.target.conf (ADR-0051). They are firmware-only disposable-test
payloads, never installable release files. The native debug-generator/private
unit verification and wrong-kernel refusal have passed. The gated host boot
launcher is prepared; actual SMBIOS import/BIOS/UEFI execution remains pending. Do not run the
probe in the build chroot as a substitute for boot: it deliberately refuses.
Use a verified cold target checkpoint in a separate disposable writable guest,
with serial TODDY-BOOT-TEST and pristine private UEFI variables, once the H09
prerequisites pass. Preserve failed logs/guest overlays for diagnosis; never
restart or copy the active builder disks to manufacture boot evidence.


After actual h09-kernel, h09-boot-config and h09-bootloader 0/0 acceptance,
create a fresh paired cold checkpoint named h09-boot-ready with the existing
stop/checkpoint procedure. Restart the builder, wait for SSH and run
mount-kernfs.sh so its guarded artifact markers can be checked. Commit/sync
H08 completed and H09 in_progress first. Then run from the project root:

```sh
python3 scripts/host/boot_test.py bios --checkpoint h09-boot-ready
python3 scripts/host/boot_test.py uefi --checkpoint h09-boot-ready
```

Run them sequentially with durable host command logs. Each prints its unique
.local/vm/boot-tests/h09-MODE-* workspace and saves an atomic result.json,
including its container ID/run ID. A timeout preserves logs/overlay and stops
only that identified test guest. If interrupted, inspect that exact container
and result.json; a missing controller observation is not guest termination.
Never start a replacement while the recorded guest is running. If result.json
reports cleanup_uncertain, establish the recorded container's real state before
continuing. The launcher also refuses any running Toddy boot-test container.

On success, review serial evidence, matching firmware/kernel, compiler/linkage,
module lifecycle, QEMU exit and unchanged checkpoint hash. This is early boot
acceptance only, not login, networking, live ISO, persistence or installer proof.
Keep failed workspaces for diagnosis; stopped containers may be removed by their
exact recorded ID after logs are retained. No blanket container cleanup is
part of this workflow. No native Toddy boot has run yet.


The prepared H10 runtime helper (ADR-0052) must run only after accepted H09 and
synchronized H10 in_progress status. Its future guest command is
python3 /opt/toddy-build/scripts/build/h10/initramfs_runtime.py. It refuses an
existing /mnt/lfs/sources/stage/toddy-initramfs-runtime directory; preserve and
inspect any partial stage before a deliberate retry. Successful staging writes
/mnt/lfs/sources/evidence/h10-initramfs/runtime.json. Inspect exact file hashes
and ownership, not just directory existence. Staging is not a completed
initramfs or native boot. The private native experiment was removed after its
checks, and the current installed root/active BDB inputs remain unchanged.


APT repository postcheck failures now preserve the printed
/tmp/toddy-apt-native.* fixture inside the native target after stopping their
HTTPS child and scoped GnuPG agent. Review its rejection.log, https.log, private
Dpkg state and source/index/payload copies together with
/sources/evidence/h07-apt/native-repository.log. Retained signing/TLS keys are
throwaway test identities, never publication inputs. Do not copy this fixture
into Git or an image. Retry uses a fresh fixture; remove the specifically
identified old fixture only after preserving the needed sanitized diagnosis.
Successful runs remove their fixture, and the original failing exit remains
nonzero. The active BDB recipe inputs were not synchronized during this review.


The private builder-kernel overlay experiment is reproducible with
python3 scripts/host/probe_overlay_acl.py off and then on. The off case is an
intentional negative control for hardlink copy-up; it must observe broken
propagation, while on must preserve it and expose index=on in actual mount
options. Both use only fresh /mnt/lfs/tmp fixtures inside a private namespace.
On failure, the printed fixture is retained after attempted unmount; verify
actual mount state before cleanup. No physical block device is opened. A native
Squashfs/live boot must repeat the metadata/ACL/hardlink/volatile-write checks;
this builder-kernel experiment cannot satisfy that acceptance (ADR-0048).


Native Kconfig preparation evidence (ADR-0046) is preserved outside installed
state at /mnt/lfs/sources/probes/kernel-config-4wfyi975 in this builder. Its
driver.log/exit retain the initial configuration and stale release observation;
prepare.log/prepare.exit retain the corrected native preparation. Both drivers
finished 0, and the latter asserts 7.1.8-toddy. A full copied evidence record is
.local/logs/h09-native-kconfig-probe.json. Do not rename this private source
into the official H09 build or count its helpers as a completed kernel. The
gated recipe performs a fresh verified extraction and repeats the accepted
configuration/preparation sequence before the actual build. Inspect these logs
if its release check differs; do not remove the suffix assertion or change the
frozen kernel to work around stale generated configuration.


Run python3 scripts/host/probe_switch_root.py to reproduce the private PID-1
root-switch experiment (ADR-0052). It prints the exact fixture path before
launching its namespace child and preserves a failure report outside Git.
On success, namespace mounts vanish and the empty fixture is removed. On a
failure or controller interruption, verify the child's actual state and mount
namespace before removing that exact fixture; never broaden cleanup to /tmp or
/mnt/lfs. The runtime roots are distinct tmpfs instances, not the installed root.
This test does not replace initramfs boot or actual Squashfs/overlay switching.


The prepared live-media identity/hash component (ADR-0053) is exercised by
python3 scripts/host/probe_live_media.py. Each run uses its own native private
/tmp/toddy-media-integrity-* fixture; failures preserve the printed path and
raw host report, while success removes the fixture. It does not mount a device
or establish ISO/Squashfs/boot acceptance. Future /init integration must supply
expected identity/hash from generated initramfs metadata, use a read-only media
mount, and treat rejection as a diagnostic/recovery condition. Never replace
an expected digest with one read from a rejected medium to bypass the check.


The prepared live /init is scripts/build/h10/live_init.sh. Its future assembly
must place matching generated identity/hash files in /etc/toddy-live, install
the integrity helper at /usr/lib/toddy/live_media.sh, and include the numeric
ACL stream at /usr/share/toddy/live-root.acl in the compressed root. Missing
metadata or an unsupported overlay profile must not be worked around by
removing checks. Actual image assembly and boot remain pending behind H09.
The proposed toddy.rescue kernel flag enters its early local console; this
console and full failure path have not yet been exercised in a booted guest.
Ordinary execution refuses before mounts. Thirty discovery passes do not
promise a hard timeout for kernel storage I/O. Live changes consume RAM and
are discarded; do not treat them as installed-system persistence.


The overlay probe now also tests a private native set-ID executable through
both overlay and direct nosuid-upper paths. Expected identities are recorded
in ADR-0048. It performs no installed account/helper changes. Reports retain
SHA-256-suffixed immutable generations before updating the unsuffixed current
JSON, so rerunning the experiment does not erase earlier cited evidence.


For apparently repeated BDB recovery headings, compare the full method/argument
line, checkpoint counter, file size/mtime and actual child process across two
observations. Recd011 deliberately waits about 7m04.5s per variant before other
work; fifteen-iteration checkpoint output is approximately 31.7s apart. See
docs/evidence/H07-bdb-wait-investigation.md. Parent do_wait and Tcl do_select
are consistent with this source-defined wait, not by themselves a deadlock.
If progress stops beyond the current case's expected work, inspect that exact
case/process and resource state before deciding on recovery. Never restart the
suite solely because a wrapper log is quiet or a heading repeats.


The prepared archive component (ADR-0054) runs only after the H10 gate with
python3 /opt/toddy-build/scripts/build/h10/initramfs_archive.py --media-id
<generated-identity> --rootfs-sha256 <actual-root-image-digest> --epoch
<recorded-epoch>. Its fixed /mnt/lfs/sources/stage/toddy-initramfs workspace
contains runtime/, cpio.log, gzip.log, both archive forms and manifest.json.
A partial/existing workspace is preserved and refused; inspect logs and exact
paths before a deliberate retry. Metadata must be derived from the actual image
assembly, not copied from the private experiment. Boot remains a separate gate.

Reproduce the isolated archive experiment with
python3 scripts/host/probe_initramfs_archive.py. It uses fresh target /tmp
fixtures, retains failure paths and content-addressed host reports, and removes
only its own successful fixtures. No active recipe synchronization is needed.
The report retains the full staged manifest, native provenance and artifact
hashes; fixture archives are not release artifacts or evidence of a boot.


Reproduce the read-only native Python QA key-marker check with
python3 scripts/host/probe_python_qa_key_audit.py. It extracts only an own,
hash-verified native archive into its printed /mnt/lfs/tmp/toddy-python-qa-audit-*
fixture. A failure preserves that exact tree and the content-addressed report;
success removes it. It never changes installed package ownership or active
BDB sources. Preserve finding paths/hashes, not private-key bodies.

After H11 becomes eligible, the prepared production component is
python3 /opt/toddy-build/scripts/build/h11/audit_private_key_material.py
/mnt/lfs/sources/stage/SELECTED-RELEASE-ROOT. Findings produce exit 1; read errors
also fail. Do not waive findings merely because some earlier QA fixtures were
public. This marker scan is only one part of the required artifact credential
audit; account/identity/provider state and unrecognized formats remain separate.


The private ownership handoff can be reproduced with
python3 scripts/host/probe_python_qa_ownership.py. It operates only on its
printed /mnt/lfs/tmp/toddy-python-qa-ownership-* workspace, uses native --unpack
with explicit private --root paths, and limits compression to two threads.
The wrong-order failure is intentional and separate from the correct-order
root. Inspect each command's captured exit/stdout/stderr in the report.
Package states remain unpacked; do not interpret them as configured acceptance.
On a failed experiment preserve its exact workspace and archives; on success
only that workspace is removed. Installed Dpkg status must remain unchanged.

For the future production transfer, retain the original archive, both prepared
new archives and the exact ownership manifest before upgrading the core. If
interrupted between core and QA, resume from actual package state and verified
archives; never force QA to overwrite files still owned by Python. The gated
production transfer/controller remains to be implemented (ADR-0049).


The H11-only --prepare-python-qa-handoff option on stage_package.py can prepare
the complete unmodified Python QA archive before its old owner releases paths.
It cannot be combined with --install. A prepared_ownership_handoff record is
not proof of installation: preserve its predecessor hashes, exact path list
and both new archives, then require a separate conflict-free install after
core ownership changes. The durable production install/controller remains
pending. Do not invoke this option during H07 or weaken the H11 gate.

python3 scripts/host/probe_python_qa_handoff_plan.py checks this preflight in a
private /mnt/lfs/tmp/toddy-python-qa-handoff-* fixture against real installed
Python provenance. It changes neither installed state nor native package cache.
Failures preserve the printed fixture and content-addressed evidence; successful
fixtures are removed. Changed installed/staged bytes or timestamps require
diagnosis, not an override.

The private ownership probe now includes a third interrupted-order root. It
kills only its newly created native unpack process group, preserves the old
archive, observes half-installed state, then reapplies core and QA and verifies
all transferred files. The observed old version can survive a failed unpack;
never infer payload completeness from Version alone. python_qa_transfer.py is
only a next-action policy: a partial state requires a matching validated
transaction before retry. It does not install, journal intent or accept the
release. The production controller still must implement those operations.
