# Development recovery

H01–H11 have produced the current foundation ISO. H12 final-media boot and failure
recovery passed; native follow-ups and H13/G1 status are in status.json. The target
root remains the designated guest /dev/vdb4 mounted at /mnt/lfs. No physical disk
is a test target. Use current evidence and the latest recovery entries below;
earlier sections retain historical failed generations and must not be mistaken
for live processes. Current artifact: [evidence/H11.md](evidence/H11.md).

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
path reported in the log. Inspect it before retrying. Private native builds and
all three roundtrips passed in ADR-0075; the gated installed package still needs
its own acceptance. Extraction cannot substitute for native-kernel live boot.


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
the integrity helper at /usr/lib/toddy/live_media.sh and ACL copy-up helper at
/usr/lib/toddy/restore_live_acls.sh, and include the numeric
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
production transfer/controller is now prepared and privately tested (ADR-0049);
full gated target execution and image acceptance remain pending.


The H11-only --prepare-python-qa-handoff option on stage_package.py can prepare
the complete unmodified Python QA archive before its old owner releases paths.
It cannot be combined with --install. A prepared_ownership_handoff record is
not proof of installation: preserve its predecessor hashes, exact path list
and both new archives, then require a separate conflict-free install after
core ownership changes. The durable production controller is described below; its gated target
execution remains pending. Do not invoke this option during H07 or weaken the H11 gate.

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
release. The prepared production controller implements those operations; actual gated
target execution and final release acceptance remain required.

After H11 is eligible and accepted inputs are synchronized, prepare both archives
with python3 /opt/toddy-build/scripts/build/prepare_python_qa.py under the normal
logged recipe runner. It is archive-only; there is no install flag. Inspect
/mnt/lfs/sources/evidence/h11-python-qa-preparation/prepared.json and verify all
listed archive/record identities before a subsequent transfer. Preserve the
original archive and both successor artifacts throughout the transaction.

A failed preparation retains /mnt/lfs/sources/stage/h11-python-runtime,
/mnt/lfs/sources/stage/h11-python-tests and its evidence directory. The command
refuses to overwrite these or an existing successor cache archive. First check
that installed Python/status are unchanged, diagnose the exact failing step,
and preserve the failed stages/artifacts under an explicitly named incident
checkpoint before reconstructing from the hash-verified original. Do not run
this recipe again after an installed transfer has begun. The prepared transfer controller must run and pass on the designated final
target, followed by final image exclusion; prepared.json is not a completion
marker for H11.


After successful eligible preparation, the separate production transfer entry is
python3 /opt/toddy-build/scripts/build/install_python_qa.py. It independently
enforces H11, reads only the fixed preparation directory and retained package
records, rehashes and re-extracts all three archives, validates the whole pair
and preserves the original archive. It uses native Dpkg install/configure with
normal dependency and conflict checks. Never use force-overwrite or remove
tracked paths manually to bypass its checks.

The fixed preparation directory contains transaction.json, transaction.lock and
numbered action logs. Intent is atomically persisted and fsynced before Dpkg
mutation. On interruption, inspect the log, actual Dpkg version/status and the
recorded archive identities; correct the diagnosed cause, then rerun the same
install command with the same artifacts. Do not rerun preparation or delete the
journal after installation has begun. An old-version half-install is retried
from the retained successor archive; unpacked/half-configured state is configured
before proceeding. A missing/mismatched transaction or an unowned residual QA
file requires diagnosis. No automatic unchanged failed-action loop is used.

Completion requires both packages configured, exact installed files/ownership,
a clean native Dpkg audit and actual Python/SSL/SQLite/QA imports. Repeating a
completed transaction revalidates without reinstalling. Candidate provenance
records are marked installed only after those checks; a crash during that final
bookkeeping can use the same command again. An action exit left null means its
exit was not captured; later verified state does not fabricate that exit code.

Reproduce the private configured interruption/recovery/idempotency test with
python3 scripts/host/probe_python_qa_handoff_plan.py --transaction. It installs
22 own source-built dependency packages into a new private root, interrupts
after real core configuration and resumes QA. The current installed target
status/cache and running DB sources remain unchanged. Reports retain the native
dependency install output, action logs, durable transaction and postconditions.
The production gate/entry itself remains unexecuted while H07 is incomplete.

Reproduce fresh live-account generation and native Shadow validation with
python3 scripts/host/probe_live_accounts.py. The private root is printed as
/mnt/lfs/tmp/toddy-live-accounts-*. A failure preserves it and the content-addressed
report; successful fixtures are removed. Native checker output is saved in the
fixture before an assertion and in successful reports. The initial incorrect
33-group assertion left fixture toddy-live-accounts-ierq40t7; the frozen book has
34 groups and the corrected run passes (ADR-0055). Installed target accounts
remain untouched. Do not copy a failed fixture into a release root.

The prepared live_accounts.stage_accounts component requires absent account/
identity files and an empty root home in its caller's fresh image stage. It
never sanitizes inherited password state in place. On refusal, preserve the
stage, fix the assembly input inventory and reconstruct a fresh stage; do not
waive the refusal or point it at the installed build target. Image/boot/login
integration is still pending, with H09/H10 prerequisites unchanged.

Reproduce explicit root-copy metadata preservation with
python3 scripts/host/probe_selected_root_copy.py. It uses native Tar and a private
mount namespace; the only tmpfs mount is a disposable negative fixture. Logs
and content-addressed evidence use .local/logs/h10-selected-root-copy-probe*.
On failure retain the printed /mnt/lfs/tmp/toddy-selected-root-copy-* fixture.
A successful run removes that private fixture after retaining its complete result.

The prepared copy_selected_root.copy_selected component requires fresh stage and
work directories. Its work directory retains selected-paths.nul, selected-root.tar,
create.log, extract.log and a successful report.json. Metadata mismatch also
writes expected.json and actual.json (digests, not xattr contents). On a failure,
inspect that evidence, preserve the failed attempt under an incident checkpoint,
correct the selection/source cause and reconstruct into new fresh paths. Do not
overwrite an existing destination or accept a source that changed during copying.
Full provenance-based image inventory, account/config generation, compression and
boot integration remain pending; this copy report is not H10 acceptance.

For the prepared package-payload image inventory, run
python3 scripts/host/probe_live_root_inventory.py. The source target must remain
quiescent for a successful final preflight. Its current H07 candidate namespace
has 63,132 paths from 124 own package records. Full inspection deliberately
refuses the still-owned Glibc /usr/share/info/dir index. The independent current
payload audit found only that known mismatch. Do not delete the index, change
its recorded hash or waive the check. Let the scheduled H07 final metadata
closure create its corrected package generation and regenerate the shared index,
then rerun and require clean installed-payload verification (ADR-0057).

The candidate inventory and failure evidence remain outside Git; they do not
constitute an approved image selection. Generated configuration, package DB,
accounts, live profile and final image audits must still be integrated. The
account component now accepts only the canonical root-owned DBus identity link;
regular identity data or different links still require preserving/rebuilding the
stage. It never follows that link to read the builder's machine identity.

Reproduce the native live-console chain with
python3 scripts/host/probe_live_console.py. It uses private PID/mount namespaces
and a new devpts instance; ordinary login attempts cannot reach builder accounts.
Success verifies both generated getty commands, native Systemd offline unit
validation, password/unprivileged refusal and unchanged account/package state.
The report is .local/logs/h10-live-console-probe.json with an immutable hash copy.
On failure preserve the printed /mnt/lfs/tmp/toddy-live-console-* fixture and its
per-session/unit logs. Do not copy a probe fixture into the release image.

The live_console.stage_console helper is only for the future fresh image stage.
It refuses existing profile inputs and a baked /run/toddy/live-session marker.
Reconstruct a fresh stage after correcting selection; never remove the guard or
point it at /mnt/lfs itself. /init requires toddy.live, establishes the marker
after verified live-root setup, and carries /run across switch_root. Missing
marker/parameter during real boot requires investigation of initramfs, GRUB and
serial logs; do not unlock root or remove unit conditions as a workaround.
toddy.rescue retains the existing early local recovery path, pending boot tests.

Before installed-system delivery, remove/exclude both 50-toddy-live.conf drop-ins
and usr/share/toddy/live.issue, establish normal console/desktop login and test
after ISO removal. Their live conditions intentionally prevent starting these
instances outside live mode. Native PTY success is not a BIOS/UEFI/USB login
pass. See ADR-0058; H07 and the H09/H10 gates remain unchanged.

Reproduce the native package-database copy and actual writer-exclusion check
with python3 scripts/host/probe_package_database.py. It copies metadata only
into /mnt/lfs/tmp/toddy-package-database-* and invokes the writer solely against
a disposable root inside that fixture. On failure retain the printed fixture,
native-lock-refusal.log and content-addressed report under
.local/logs/h10-package-database-probe*. The original timestamp-assertion failure
is preserved at toddy-package-database-woon9hfr (ADR-0059). Successful fixtures
are removed after their complete per-file evidence is retained outside Git.

For eventual image integration, package_database.stage_database accepts only
absent destinations or the reviewed empty root-owned Dpkg directory layout in
guest tmp/staging storage. Any existing state requires diagnosis and a fresh
stage, never an in-place merge. Do not delete/unlink a lock to bypass a writer.
An active writer refusal means wait for that exact transaction to finish, inspect
its result, and retry at the next quiescent boundary. Interrupted copy leaves its
partial destination for diagnosis; after preserving it, reconstruct a new stage.
Process exit releases POSIX locks without manual lock-file removal.

The snapshot must correspond to the same accepted payload generation used by the
image. Repeat after final H07 metadata closure and any native QA ownership
transfer. It does not authenticate stored MD5 values, prove dependency closure,
or waive the shared Info-index payload mismatch. Require independent archive/
payload verification and native Dpkg/APT checks before release acceptance.

Reproduce the corrected native offline service policy with
python3 scripts/host/probe_offline_services.py. It uses source-owned units and
presets in a fresh /mnt/lfs/tmp/toddy-offline-services-* root and never starts
services. Failure preserves that fixture and native-preset-all.log; raw reports
are .local/logs/h08-offline-services-probe* with immutable hash copies. The
original preset failure is retained at toddy-offline-services-8nmlgzef.

After H07 acceptance and synchronized H08 status, the existing base-config
recipe calls h08/offline_services.py; its postcheck calls the same CLI --check.
Do not dispatch these production entries while the H07 recipe is active. An
unexpected unit/link/ownership state must be diagnosed from the captured native
command output; do not force replacement of an unrelated configuration link.
Use a fresh private image stage after a failed image configuration attempt.

DBus socket state must be static with the verified vendor wants link. Waiting
for a literal enabled result would repeat the original defect. The one deliberate
wait-online mask prevents networkd's Also= from undoing the offline policy when
presets are reapplied. On an installed Toddy system, an owner who wants blocking
network-online behavior can run systemctl unmask systemd-networkd-wait-online.service
followed by systemctl enable systemd-networkd-wait-online.service. Those are
owner configuration changes on Toddy, not workstation recovery commands.
Do not remove other masks or relax arbitrary ownership-audit failures. Native
boot/DHCP/DNS and offline boot timing remain H08/H12 verification obligations.


Reproduce fresh live filesystem/time/resolver preparation with
python3 scripts/host/probe_live_configuration.py (ADR-0061). It uses a private
/mnt/lfs/tmp/toddy-live-configuration-* root and the prepared base candidate,
without installing it. Native Findmnt/Date/Systemd output and eleven negative
cases are retained in .local/logs/h10-live-configuration-probe*.json. Failed
fixtures remain for diagnosis; successful ones are removed after reporting.
An interrupted configuration attempt requires a fresh image stage, not an
in-place retry. Final assembly must obtain fstab identity from the accepted H08
package, preserve its conffile metadata, account for the live transformation,
and rerun native checks. Actual boot mounts and DNS remain unverified.


Reproduce fresh native documentation-index generation with
python3 scripts/host/probe_info_index.py (ADR-0062). The private fixture is under
/mnt/lfs/tmp/toddy-info-index-*; failure preserves it, successful validation
removes it. Raw reports and immutable SHA-256 copies are kept in
.local/logs/h10-info-index-probe*.json. Preserve a failed or interrupted index
stage and reconstruct from accepted inputs; do not merge unknown output or
remove the installed source index to make the preflight pass. The final H10
caller must use the accepted post-H07-closure package inventory. This component
refuses an index still listed as package payload and does not resolve that
outstanding metadata transition itself.


Reproduce native loader-cache preparation with
python3 scripts/host/probe_loader_cache.py (ADR-0064). Private roots are under
/mnt/lfs/tmp/toddy-loader-cache-*; failures preserve their state and successful
fixtures are removed after evidence collection. The original layout-refusal
fixture is toddy-loader-cache-hq68ba74. Raw reports and immutable hash copies
are .local/logs/h10-loader-cache-probe*.json. Full-image integration must pass
the accepted package inventory after H07 closure; the current probe validates
only its declared native library subset. Never copy builder caches, change the
owned /lib64 layout to match the minimal initramfs, or overwrite an interrupted
image cache. Preserve it and reconstruct a fresh stage. Additional loader search
configuration/tunables need a reviewed extension to the frozen foundation policy.


Fresh image accounts now include the explicit _apt UID/GID 100 service identity
(ADR-0065); the book-only 14-user/34-group probe is historical evidence. Current
reproduction is python3 scripts/host/probe_live_accounts.py, followed by
python3 scripts/host/probe_live_console.py after account policy changes. Expect
15 users/35 groups, clean native Shadow checks, native UID/group 100 download
fixture write and root-only fixture denial. Actual APT acquisition remains
pending, including effective worker identity and absence of root fallback.
The prepared repository acceptance wrapper now rejects the frozen APT warnings
for missing sandbox identity or unsandboxed root downloads, even with exit 0.
Do not synchronize this recipe into the active H07 dispatcher; use the next
successful quiescent boundary. Preserve any failed APT fixture and fix account/
path access rather than disabling sandboxing or allowing the warning.


Reproduce native ACL capture/restore with
python3 scripts/host/probe_acl_sidecar.py. It uses a private guest mount namespace
and /mnt/lfs/tmp/toddy-acl-capture-* fixtures; any temporary mount is unmounted
on exit. Successful fixtures are removed, failures are retained. Raw evidence
and hash copies are .local/logs/h10-acl-capture-probe*.json. A failed or interrupted
image capture must preserve its existing sidecar/.part file and reconstruct a
fresh stage. Do not truncate it, ignore a cross-filesystem refusal, or suppress
ACL diagnostics. Capture belongs after all final image configuration; any later
permission/payload change requires a newly generated image/sidecar and audit.
The first bytearray decoder failure remains at toddy-acl-capture-x3rudrac.
Actual private Squashfs/overlay restoration passed with the ADR-0075 correction;
complete-image and native Linux 7.1.8 boot restoration remain pending.


Reproduce fresh mutable-directory generation with
python3 scripts/host/probe_fresh_directories.py (ADR-0066). The probe runs in a
private guest mount namespace, removes its successful fixture and preserves any
failed fixture. Its initial device-layout error remains in
/mnt/lfs/tmp/toddy-fresh-directories-9zoyrodt. Hash-addressed raw reports are
.local/logs/h10-fresh-directories-probe*.json. The image assembly order is explicit
payload copy, fresh directories, fresh accounts/configuration, derived caches,
then final ACL capture/audits. Do not copy builder cache directories, merge a
partial stage, or recursively chown existing image data to suppress a refusal.
APT partial directories use image UID 100 and GID 0; APT acquisition is still
unverified. Re-run the full root inventory after real H07 metadata closure.


The image database lock now supports nested source transactions (ADR-0059).
Reproduce with python3 scripts/host/probe_package_database.py. Require native
writer refusal after inner context exit/exception and success only after the
last context ends; the full nested database copy must preserve both source
locks. Do not work around a lock refusal by deleting locks, reopening/closing
the locked inode elsewhere, or bypassing the shared context manager. The
pre-fix reproduction remains at /mnt/lfs/tmp/toddy-package-database-heol_10o.
A failed copy is preserved; retry into a fresh stage after diagnosing its cause.


Current Berkeley DB investigation (ADR-0067): the original driver 1364/runner
1365 remains active, but its partial ALL.OUT has repmgr007 and repmgr100 FAIL
entries. APT remains success-gated and must not start from this result. Do not
sync active inputs or restart the same missing-helper configuration. The private
fixture is /mnt/lfs/tmp/toddy-repmgr-diagnosis-w59p805n. Original race reproduction
exit 12, corrected three-case exit 0, and C++ helper build exit 2 are preserved
in original.*, corrected-driver.* and cxx-driver.* respectively. The source
test/repmgr/db_repsite.cpp is absent upstream; it is not an installation approval
issue. The prepared patch changes only bounded diagnostic waiting.

Next inspect the separate all-twenty-case run, launched as guest PID 1073235:
python3 scripts/host/vm.py ssh 'tail -n 30 /mnt/lfs/tmp/toddy-repmgr-diagnosis-w59p805n/other-repmgr-driver.log; if test -f /mnt/lfs/tmp/toddy-repmgr-diagnosis-w59p805n/other-repmgr-driver.exit; then cat /mnt/lfs/tmp/toddy-repmgr-diagnosis-w59p805n/other-repmgr-driver.exit; fi'

That driver uses a private network namespace, native tester/Tcl/library, a
3600-second limit and an explicit terminal exit file. Inspect its process when
the exit is absent; never restart from an observation timeout. Resolve actual
multi-process helper support with native operations and unchanged assertions;
no source-availability exception has been accepted. Then freeze the tested
patch and update the fresh/recovery build path at a quiescent boundary. Preserve
complete original-suite logs and zero-install postconditions before any retry.


Berkeley DB multiprocess adapter probe (ADR-0068): first-three driver exited 0;
its log is multiproc-driver.log and preserved data is source/build-multiproc/
first-three.TESTDIR under the existing toddy-repmgr-diagnosis-w59p805n fixture.
The complete eleven-case run is guest PID 1076295, with
multiproc-all-driver.log/.exit/.pid in that fixture. Inspect the exit and log
before retrying; a missing exit file alone is not a failure. The bounded driver
uses timeout 3600 with kill-after 30 and a private network namespace. The
committed entry point is berkeley-db-multiprocess-regression.tcl. Current helper
source is test-only and has not been integrated into active build inputs.
Preserve any failed log/TESTDIR; diagnose actual operations before correction.


The complete private multiprocess run exited 0 with all eleven cases; inspect
ADR-0068 for terminal log/source/binary hashes. The twenty-case other_repmgr run
is still independent and must be inspected. Prepared fresh/recovery recipes now
build the pinned test-only helper and apply/verify both frozen fixture patches.
After the original driver ends, preserve its final logs and confirm the failure
record/zero installed changes before any sync or corrected dispatcher launch.
Do not accept its two FAIL lines merely because isolated corrections passed.
If helper compilation leaves db_repsite.new, preserve and inspect it before a
retry; the recipe refuses to silently overwrite an interrupted output.
Reproduce input-only validation with
python3 scripts/host/probe_db_test_fixtures.py. Its private directory is retained
in .local/probes/db-fixtures-*; the report never claims native suite acceptance.


Both private replication-manager groups are now terminal and passed: 20 cases
in other-repmgr-driver.log and 11 in multiproc-all-driver.log. Exact exit/log
hashes are in ADR-0067/0068; both original upstream case lists are intact.
Session-specific guarded continuation is prepared at
.local/scripts/h07-repmgr-continuation.py. Its --inspect mode is read-only and
currently reports ready=false while original driver 1364 remains active.
It requires the exact two diagnosed failures, the upstream complete failed-suite
summary with no additional unexpected output, recipe exit 1, no postcheck and
zero changed installed paths. It archives terminal logs/manifest before sync;
any unknown result or changed reviewed input stops for diagnosis, never retries
unchanged inputs automatically. Corrected dispatch keeps the same h07-berkeley-db
step ID and verifies the cached compiled build before rerunning the full suite.
Only a later actual 0/0 result may launch the final-base driver. No automatic
milestone acceptance or H08/Phase 2 progression is part of this supervisor.


Current Berkeley DB execution supersedes the earlier serial continuation
(ADR-0069). Host supervisor 942158 was deliberately disarmed while waiting; its
state is superseded_by_isolated_parallel_standard_run. Do not restart that
supervisor or launch another full suite. Original guest driver 1364/runner 1365
still collect later tests with the two diagnosed FAIL entries.

The corrected complete run is guest driver 1107192, fixture
/mnt/lfs/sources/recovery/db-standard-nfv62s4o. Inspect driver.log, running.json,
driver.pid, test.exit, driver.exit and result.json there, plus source/build-test/
ALL.OUT. A missing exit is not failure; inspect the PID before any retry.
The protected input manifest hash is
336abd7ca1442e5102249da2f774b30326e06d268cd2b16b65fc81e8c333e6f9.
The driver has no installation branch. Complete-suite success must be followed
by validated production handoff under the normal exclusive runner lock, after
the original failure and zero-installed-change audit are preserved. That handoff
is now prepared below but not positively accepted yet; do not fabricate a success
marker from private logs. The ordinary fresh recipe still runs the complete
standard suite itself.

The initial private attempt remains at db-standard-yc87i9pi with interruption-
reason.json, test exit -9, driver exit 1 and protected result-evidence. It was
stopped to restore tmpfs semantics, not from a timeout. The nfv62s4o fixture also
retains the first rejected findmnt-based probe and the corrected statfs probe.
Native input-rejection evidence is in db-standard-input-rejection-weajsa4_.
Session setup/launch observations are .local/logs/h07-parallel-standard-*.json;
older generations are retained with hash suffixes. See ADR-0069 before changing
active inputs, namespace mounts or interpreting any terminal result.


The completed isolated-result gate is now prepared at
scripts/build/db_standard_result.py (ADR-0069). After terminal success and a
verified quiescent input sync, run in the guest:
python3 -B /opt/toddy-build/scripts/build/db_standard_result.py /mnt/lfs/sources/recovery/db-standard-nfv62s4o
It must reject the run while unfinished. It does not install, mark a package
accepted or waive the original terminal installed-change audit. Production
handoff is prepared below and must be exercised after full native success.


The production handoff is now prepared (ADR-0069) but must not run until both
full drivers are terminal and the corrected result is successful. The following
sequence is the intended next production path; its positive execution remains
pending. First preserve and inspect both driver exits/logs. Any unknown failure
requires diagnosis. At the quiescent boundary sync the committed build inputs
with python3 scripts/host/sync_build.py, which transfers the frozen fixture patch
and result verifiers. Then, inside the guarded guest, run:

```sh
python3 -B /opt/toddy-build/scripts/build/db_standard_handoff.py prepare /mnt/lfs/sources/recovery/db-standard-nfv62s4o
cd /opt/toddy-build/scripts/build
python3 run_step.py h07-berkeley-db h07/berkeley-db-verified-production.sh h07/berkeley-db-check.sh --user root
```

Use a detached driver with durable log/PID/exit files for the dispatcher, as
for other long recipes. Preparation refuses an active runner, any additional
original failure, changed installed paths, incomplete corrected output or an
existing nomination. Never remove a nomination/running marker to force a retry.
After interruption inspect candidate.json in the copied evidence, the protected
original history, production staging and the normal manifest before deciding
whether to resume or restore the paired checkpoint. A staged package alone is
unfinished. Only actual recipe/postcheck 0/0 may unblock APT. Keep the original
success-only and obsolete serial-retry supervisors from launching duplicates.


APT's next committed input sync includes ADR-0070's explicit runtime seccomp
setting and the worker observer. The full apt-check.sh runs it during actual
HTTPS installation and preserves /sources/evidence/h07-apt/https-worker.json.
Inspect command_exit, expected executable, IDs/groups, capabilities and additional
filter count together with native-repository.log; an empty/missing observation
is not acceptance. Before retry preserve any existing observer report and failed
repository fixture. If APT traps a syscall, keep its exact diagnostic and native
logs; do not disable the selected filter or add broad exceptions as a shortcut.
The observer preflight can be repeated independently with
python3 scripts/host/probe_apt_worker_observer.py; it does not test APT itself.


The final image's optional Python QA exclusion is prepared in
scripts/build/h11/remove_image_qa.py (ADR-0071). Invoke it only from the gated
assembler after actual H11 ownership transfer and fresh payload/database staging.
Keep its intent journal and native purge log outside the image. A native exit 0
with complete=false is a failure: preserve that partial image, diagnose residual
QA paths or metadata, and rebuild a fresh stage from verified inputs. Never
remove tracked files by hand or reuse a partial attempt to force acceptance.
Run final caches/indexes/ACL capture and package/credential audits after exclusion.
Reproduce the private operation with
python3 scripts/host/probe_python_qa_handoff_plan.py --image-removal.
The exact six OpenSSL documentation-marker classifications can be reproduced
with python3 scripts/host/probe_openssl_document_markers.py; retain raw scanner
findings and require the exact reviewed hashes. This is not a whole-image
credential pass and does not cover altered/new findings or arbitrary secrets.

Use h11/review_image_key_markers.py for the staged image's narrow armor-marker
review after the H11 gate. Keep its complete raw_scan, qualified examples,
unresolved findings and provenance together. A passing marker check does not
complete credential or image acceptance. Changed document bytes, unknown paths,
incomplete native identity/provenance or a parser discrepancy require diagnosis;
do not modify the reviewed constants to bypass a finding. The private component
probe is python3 scripts/host/probe_image_key_marker_review.py. It retains its
native log and all results under .local/logs/h11-image-key-marker-review-<sha>.log;
unexpected failures preserve the printed disposable fixture path.


Root assembly (ADR-0072) preserves assembly.json and numbered component reports
in its separate private evidence directory. An unfinished action timestamp or
assembled=false means incomplete work even if a root directory or Tar exists.
Inspect its stage, native failure output, reports and source stability before
retry. Preserve that generation and select two new paths; no in-place resume,
merge or overwrite mode exists. The CLI owns the exclusive build lock itself,
so do not nest it under run_step.py.

Current source readiness refuses the known H07 /usr/share/info/dir obligation
from ADR-0057. Complete normal H07 metadata closure, then H08/H09 acceptance;
do not remove that index or rewrite records during the active Berkeley suite.
Private reproduction: python3 scripts/host/probe_root_assembly_preflight.py.
This diagnostic expects today's incomplete H07 state and must be revised after
real closure, not used as a permanent positive production test. Independent
payload checks: python3 scripts/host/probe_image_key_marker_review.py --payload.


For an image-attribution failure (ADR-0073), inspect missing, unknown, changed
and hardlink_groups_match in the separate report. Compare the declaration plan
with its named package/generator and preserved copy input manifest. Do not add
an observed unexpected file to the plan to force acceptance, delete unknown
state from a failed generation, or disable xattr/hardlink checks. Diagnose its
producer, correct the implementation and assemble a new generation. The native
component probe is python3 scripts/host/probe_image_key_marker_review.py --attribution;
its full-profile assembly/boot fields deliberately remain false.

For an image-runtime-audit failure (ADR-0074), inspect the exact executable,
PT_INTERP or shebang, and the native loader diagnostic. Compare provider paths
with image attribution and package provenance. A provider installed in the builder
does not satisfy an absent image file. Preserve the failed generation; repair the
package/declaration/assembly cause and create a fresh generation. Do not inject
builder library paths, disable the audit, or claim optional dlopen/data coverage
from a successful --list. The native --runtime probe preserves its failed fixture
and reports its path; its successful fixture is removed only after log capture.

ADR-0075 supersedes direct Squashfs ACL restoration: use the initramfs
restore_live_acls.sh helper before Systemd. If restoration fails, remain in the
existing rescue path. Inspect the exact sidecar name, physical parent, upper
filesystem support and effective index=on mount option. Never drop ACL records,
disable indexing or start services with incomplete permission restoration.
The helper copies only named files/directories up with unchanged modes; RAM
exhaustion or a malformed path must fail visibly rather than changing policy.

Private native tool experiments retain inputs.json, running.json, driver.pid,
driver.log, each stage's log/exit, result.json and driver.exit.json below the
printed /mnt/lfs/sources/recovery/squashfs-native-* directory. Use
python3 scripts/host/probe_native_squashfs.py collect PRINTED_FIXTURE to inspect
that process/results. Never restart a live experiment because an observation
expired. Preserve failed generations; a new start chooses a fresh directory.
A successful experiment is not h10-squashfs-tools.success.json. The gated
production package must still pass its own build/roundtrip and boot checks.

For compression failures (ADR-0076), inspect compression.json's last step/exit,
that native log, superblock.json and the two comparison reports. complete=false
or an unfinished step remains incomplete even if rootfs.squashfs exists. Preserve
all failed output and the original source manifest. Diagnose changed input,
unknown xattrs, metadata/hardlink mismatch, insufficient storage or native tool
failure; correct the cause and select a new generation. Do not drop failed
comparisons, alter the expected manifest to match output, append to an existing
image or suppress Unsquashfs errors. The two-hour timeout has a kill-after grace
for its own process group. Observe its existing process before attempting retry.
Successful compression does not waive remaining release/boot checks.

Private native ISO-stack preparation (ADR-0077) uses
`python3 scripts/host/probe_native_libburnia.py start` and
`python3 scripts/host/probe_native_libburnia.py collect PRINTED_FIXTURE`.
The protected `/mnt/lfs/sources/recovery/libburnia-native-*` generation retains
verified archives/inputs, every configure/build/private-install log and exit,
stage intent/timeout, actual linkage/version output, roundtrip evidence and
terminal result/driver exit. Inspect the live PID before retrying. No global
install, package success marker, active-input sync or physical media operation
belongs to this experiment. Only the private prefix is an installation target.
Preserve failed generations; use a fresh generation after correcting a cause.
The native production recipes remain subject to the H11 gate and their own
package postchecks. An experimental file-only ISO is not the foundation ISO.

Private Mtools and loader-only media recovery (ADR-0078): inspect the printed
`mtools-native-*` driver PID and result/exit files with
`python3 scripts/host/probe_native_mtools.py collect PRINTED_FIXTURE`.
The media probe retains `/sources/recovery/grub-media-*` stage intents/logs/exits
and its result; host `.local/vm/grub-media-tests/probe-*` retains native input/logs,
transferred ISO, exact QEMU commands, container IDs, firmware vars, serial logs
and final states. On an SSH observation timeout, inspect the recorded native
PID/stage before retrying; do not infer terminal state from lost transport.

Firmware tests share the native boot-test lock and reject existing labeled test
containers. Their 45-second deadline records failure and stops only the matching
owned container. Keep failed logs: a clean QEMU exit without the exact platform
marker and ISO data read is failure. Never start duplicates, attach the builder
disk or change a physical disk to diagnose media boot. Correct inputs and use a
fresh generation after verifying the old run has terminated. The final accepted
loader-only fixture is not a recovery image or a completed H09/H11/H12 gate.

Database progress correction (ADR-0079): observe each run with
`python3 scripts/host/observe_bdb.py --corrected-fixture PRINTED_FIXTURE`.
The original log is /sources/evidence/h07-berkeley-db/standard.log; corrected
uses its own fixture/standard.log. Only their outer Running headers establish
the current group. TestNNN and RecdNNN recur inside earlier groups. At the
corrected 2026-11-07 08:36 UTC snapshot, original is group 27/hash method 8 of 9,
but corrected is only group 19/compression. Old claims that both had reached
27/27 were reporting errors. Never combine the original's later position with
the corrected run's zero-failure count.

The versioned observer verifies frozen source/configuration hashes, complete
header order, actual PID identity and terminal files. It retains full outer
log snapshots, detailed last dispatch arguments and any observation-time group
transition. A mismatch means progress is unknown and needs investigation.
Do not execute run_std -n inside a live tree: the frozen implementation removes
and recreates ALL.OUT even in that mode. Do not alter test input or restart a
process to obtain a progress estimate. Existing strict full-result/production
handoff criteria remain unchanged; this observer cannot accept a package.

Fresh-image identity audit recovery (ADR-0080): inspect the preserved
fresh-identity-audit report and assembly journal. A declared or owned credential
is still a failure. Correct the originating recipe or explicit copy selection,
then create a new stage; never delete credentials in place and relabel the old
stage accepted. Keep unexpected content private. The probe retains failed
temporary roots, removes successful ones and saves a content-addressed log.
It does not operate on installed user accounts and grants no whole-image
credential or first-boot acceptance.

Compression-bound initramfs recovery (ADR-0081): preserve a failed generation
and inspect its native cpio/gzip logs, archive manifest and compression input.
A compression report without assembly_binding or an initramfs manifest without
compression_binding is not a production handoff. Recheck original assembly,
source manifest, native stage exits/logs and actual root artifact before choosing
a fresh generation. Never repair a stale hash, flip the profile flag or reuse
the intermediate output to force release acceptance. The CLI selects H10 or
H11 --release gates explicitly and refuses active dispatcher/sync state.

Bound hybrid-media recovery (ADR-0082): inspect result.json and each recorded
native stage/exit/log in the failed ISO generation. Preserve all original input
generations and output; the composer refuses existing outputs. Recheck native
package/archive provenance, compression binding, actual archive contents and
kernel/module generation before using a fresh output path. Missing SHA256SUMS
or complete=false remains unfinished. A successful loader-only probe cannot
be substituted for an H11 release or native-kernel recovery test.

2026-11-07 original Berkeley terminal update: driver 1364 exited 1 with zero
installed changes. The prepared handoff now correctly refuses additional output
beyond its two anticipated failures. Preserve that refusal and all terminal
reports. Reproduce the bounded native classifier diagnosis with
`python3 scripts/host/probe_bdb_output_diagnostics.py`. Test142's informational
spacing and ten recovery-coverage warnings require source-backed resolution;
never remove lines, flip exits, accept zero FAIL alone or weaken the strict gate.
Corrected driver 1107192 remains active with immutable inputs. Do not sync or
modify those inputs. Finish diagnostic work independently, then inspect its
actual complete result before selecting a reviewed correction/handoff strategy.

Recovery-coverage diagnostic (ADR-0083): the completed passing fixture is
/sources/recovery/db-standard-coverage-0_05jaht (prepend /mnt/lfs outside chroot).
Use `probe_bdb_recovery_coverage.py --collect PRINTED_FIXTURE` to recheck terminal
exits, source hashes and raw reports without launching work. Its result is
explicitly not full-suite/package acceptance. The earlier failed diagnostic
fixtures are retained. Launch without --collect only for a deliberate new
experiment after reviewing its current source and all previous terminal states;
no new full run_std is dispatched by this probe.

Complete Berkeley diagnostic review (ADR-0084): the original-history validator
now recognizes only the exact independently rechecked terminal reports, while
retaining their exit 1 and two real failures. Actual premature prepare still
refuses the live corrected run and creates no candidate/history archive.

After the corrected driver actually terminates, first inspect its result.json,
report hashes and exit files. For the known exit-1 summary profile, the prepared
review command after a safe quiescent code sync is:

```sh
python3 -B /opt/toddy-build/scripts/build/db_standard_review.py \
  /mnt/lfs/sources/recovery/db-standard-nfv62s4o \
  --coverage /mnt/lfs/sources/recovery/db-standard-coverage-0_05jaht
```

This command preserves actual exits and writes a separate private review only.
It is not a production nomination and does not seal source custody. Inspect all
assertions and unknown diagnostics; new output requires new diagnosis. Complete
positive review and any source-qualified production handoff remain pending.
The existing strict success gate must not be bypassed by manually creating a
candidate, rewriting its result or changing recorded exits.


## Private native kernel compilation (ADR-0085)

The independent experiment is `/mnt/lfs/sources/recovery/kernel-native-dn1rodsa`
in the disposable builder; initial driver PID 3871397. It does not own the
production build dispatcher and must not be mistaken for an H09 package build.
Do not reboot the builder or modify/synchronize the active Berkeley inputs.

```sh
python3 scripts/host/probe_native_kernel.py collect /mnt/lfs/sources/recovery/kernel-native-dn1rodsa
```

Inspect the actual driver and stage processes, attempt logs/exits, completed
stage records and result.json. Live source/configuration/build output is not
terminal success. Initial source/configuration stages passed; compilation was
still running at the recorded checkpoint. Each stage has a durable log and
actual exit; a terminal successful result must also have driver exit zero.

After a genuine terminal failure, diagnose its attempt/error.json and stage
log. If the correction leaves frozen input/compiler bytes unchanged, resume
that exact generation without clearing source/configuration/build checkpoints:

```sh
python3 scripts/host/probe_native_kernel.py resume /mnt/lfs/sources/recovery/kernel-native-dn1rodsa
```

This refuses a live supervisor or still-existing detached stage child. Do not
restart merely because SSH timed out or a supervisor disappeared. If extraction
is partial, or inputs/native package state changed, preserve the fixture and
review before choosing a fresh generation. Do not rewrite completion records,
change input hashes to match modified files, or call mrproper on a completed
build just to retry collection. A fresh independent experiment can be launched
with `python3 scripts/host/probe_native_kernel.py start` only after earlier
processes are terminal; all old logs remain. This command does not install a
kernel or accept any milestone. The production recipe still requires H08.


After the private kernel finishes with verified actual driver/stage exits zero,
the independent diagnostic boot command is:

```sh
python3 scripts/host/probe_kernel_boot.py /mnt/lfs/sources/recovery/kernel-native-dn1rodsa
```

It preserves reports under .local/vm/kernel-smoke-tests and a new guest
sources/recovery/kernel-smoke-* fixture. It uses a separate diskless guest,
never the active builder disk, and records exact Docker/QEMU arguments, serial
logs, exits and hashes. An interrupted boot must be inspected using its saved
container ID/label before another test; a running labelled guest is refused.
Native full boot/login, ISO boot and H09/H12 acceptance remain separate. The
current early invocation was an expected live-kernel refusal; no kernel boot
has passed yet. Do not reuse that failure as a later passing result.


### Completed private kernel checkpoint — 2026-11-07 10:02 UTC

The kernel driver is terminal with exit zero, all five stages passed and the
private module stage contains 20 modules. The watcher in
.local/scripts/watch-native-kernel.py also terminated with exit zero after both
actual diagnostic BIOS/UEFI boots passed. Its local state is
.local/logs/h09-native-kernel-watch.json; final exit is
.local/logs/h09-native-kernel-watch.exit.json. Do not launch another watcher or
rebuild this completed generation to recover an interrupted collection.

Native boot preparation: `/mnt/lfs/sources/recovery/kernel-smoke-6omiesjt`.
Host artifacts: `.local/vm/kernel-smoke-tests/probe-d2evqi6m`, including
result.json, driver.exit.json, per-firmware serial.log/intent.json/exit.json and
terminal.json. The two owned QEMU containers were stopped and removed after
actual clean power-off. The original builder and Berkeley suite remain active.
Inspect the retained evidence; successful diagnostics are not a full-root boot.

Next dependent kernel work is final gated packaging/bootloader and complete
foundation boot after H07/H08. Current H07 remains at the complete corrected
Berkeley run; its terminal review and strict-summary qualification are still
required before production install/APT. See docs/evidence/H09-private-kernel.md
for hashes and explicit scope. The earlier preflight/live-kernel refusals remain
preserved as negative evidence, not overwritten by these later successes.


## Protected completed database coverage (ADR-0086)

The completed `/mnt/lfs/sources/recovery/db-standard-coverage-0_05jaht` generation
now contains root-private source-custody.intent.json and source-custody.json.
All 10,606 source entries are root-owned, its parent/source directories are
0700, and native tester access is denied. Raw test outputs, source bytes and
actual 0/0 exits remain unchanged. The current complete-suite review requires
this proof; its separate source remains live and must not be sealed yet.

`python3 scripts/host/seal_bdb_coverage.py` verifies/returns the existing receipt
without changing it, and exercises actual held-descriptor and access boundaries.
Do not delete the receipt or rewrite the original result to claim acceptance.
If custody was interrupted, retain the intent and closed path gate, inspect any
reported actual PID/descriptor/mapping, and retry only after it genuinely ends.
A missing supervisor or observation timeout is not sufficient. Do not kill the
unrelated complete standard suite or loosen permissions to bypass a refusal.

The first post-seal test failed because runuser is absent from the target;
sealing itself had completed. Native Python now switches to the actual tester
identity and confirms open returns PermissionError. The idempotent retry and
read-only verification passed, with the same receipt SHA-256
0a2b9b17cf57a0de76dc20ce426f784c4e92aa401d44a1d3f43817726e6dccb2.
Full standard-result qualification/production installation is still pending.


## Prepared complete-run qualification (ADR-0087)

The still-live corrected suite has no qualification or full-source custody
record. Do not modify its source or synchronize shared build inputs while it
runs. On actual terminal completion, inspect driver/test exits, every failure
and the complete independent review. If the raw run passes, keep the strict
success path. Only the exact known failed-summary diagnostic profile may use
the prepared command after a safe quiescent input sync:

```sh
python3 -B /opt/toddy-build/scripts/build/db_standard_qualify.py qualify /mnt/lfs/sources/recovery/db-standard-nfv62s4o --coverage /mnt/lfs/sources/recovery/db-standard-coverage-0_05jaht
python3 -B /opt/toddy-build/scripts/build/db_standard_qualify.py verify /mnt/lfs/sources/recovery/db-standard-nfv62s4o
```

This requires actual complete review and protected coverage before any full
source ownership change. It preserves raw results, protects full source, repeats
review and publishes a separate qualification only if everything agrees. The
positive full invocation has NOT run. A qualifying record is not a package
success; production handoff still uses strict verify_completed. Complete and
verify the production integration only after actual positive native evidence.

Preserve source-custody.intent.json/source-custody.json after interruption;
retry the same complete review and immutable source instead of restarting the
suite. JSON publication is exclusive and atomic; a leftover .pending-* file is
not an accepted record. Do not overwrite existing records or normalize a raw
exit to zero. A changed assertion/diagnostic profile needs fresh source-backed
investigation. Portable fresh-build runner/diagnostic handling is still required
before H07 acceptance; the current recovery profile pins measured inputs.


### Verified final-review source availability

The shared /opt/toddy-build input set still lacks db_standard_review.py and
db_standard_qualify.py; /mnt/lfs/sources lacks the frozen repmgr007 patch. This
is an expected deferred deployment, confirmed by read-only inspection. After
actual full-run termination and quiescence, `python3 scripts/host/sync_build.py`
transfers the committed modules, supplemental lock and missing frozen patch.
Do not attempt the prepared guest CLI before that sync, and do not sync early.

While the suite remains live, `python3 scripts/host/probe_bdb_review_inputs.py`
verified the exact reference privately: 483 Tcl files and 460 compiled seed
files match, with no shared archive or active source modifications. Retained
reference: /mnt/lfs/tmp/db-review-inputs-gb5tx0go; raw report SHA-256
432eb23619a42d72bd8779be0e16744df594230efdab5a77987d416a5a95d32a.
This is source/provenance readiness, not completion of the native suite.

## Versioned private DB preparation (ADR-0088)

The actual new preparation probe passed in
/mnt/lfs/sources/recovery/db-standard-z4zf__8c. Its preparation.json and
isolation-probe.exit record preparation only; there is no running standard
producer for this generation. Do not confuse it with the active full attempt
at db-standard-nfv62s4o or launch another full suite from it.

The preparer prints its generation path immediately and preserves
preparation.intent.json, inputs.json and probe output. On interruption inspect
that exact generation and any actual process before acting. An absent final
preparation.json is unfinished preparation, not a successful suite. Do not
manually manufacture the final record or overwrite partial evidence. A new
private preparation may be created after the prior preparation is confirmed
terminal; no completed compilation or long test run needs restarting for this.

The current normal recipe still needs this component wired into a portable
runner and result/provenance gate. Its prepared generic manifest deliberately
does not claim the historical seed profile required by the recovery acceptance
verifier. Keep native compilation provenance and full-suite acceptance separate.

## Fresh native DB compilation checkpoint (ADR-0089)

The private build /mnt/lfs/sources/recovery/db-native-m3pjqwd2 is complete:
driver 4055451 terminal, all five stages and actual C tests exited zero. Its
prepared /mnt/lfs/sources/recovery/db-standard-6gav6kkh has no standard producer.
Keep the existing complete run at db-standard-nfv62s4o as the sole active suite.

Use `python3 scripts/host/probe_native_db.py collect FIXTURE` to inspect actual
logs, PIDs and exits. `resume FIXTURE` refuses a live driver/recorded compiler or
a completed result. Completed stages are reused only with matching input/command/
log evidence. Diagnose a failed stage before retrying; do not retry an unchanged
patch/extraction failure over a partially modified tree. Preserve that generation
and use a new one for corrected source preparation after confirming termination.
An interrupted preparation after native-build.json requires inspecting the
printed PREPARATION generation and actual processes; do not infer its subprocess
ended merely because the supervising process disappeared.

The protected build-context-status snapshot preserves the actual native package
context; input and native-build digests bind it. Source/build receipts and the
verification output remain distinct from full-suite acceptance. The verifier
requires the same reviewed code snapshot as the executed build. Future recipe
changes must preserve the earlier snapshot/evidence rather than rewrite it.

## Separate standard-result provenance paths (ADR-0090)

The current active db-standard-nfv62s4o execution still belongs to the historical
460-file seed profile. Keep its original records and default result/qualification
commands. Do not add --native-build to reinterpret that running generation or
replace its manifest with db-standard-6gav6kkh's newly compiled inputs.

The latter prepared generation has no standard producer and is correctly refused
by both completion interfaces. Fresh strict results require their exact verified
native-build receipt and prepared input digest. The private actual refusal probe
is `python3 scripts/host/probe_db_native_build_result.py /mnt/lfs/sources/recovery/db-native-m3pjqwd2 --unfinished-standard-gates`;
it checks the current unfinished state and historical coverage custody without
starting tests or changing source metadata. Do not rerun it once the full suite
is terminal expecting the old live-state assertion to remain true.

## Database production output/source separation (ADR-0091)

Private production generation /mnt/lfs/sources/recovery/db-production-nlsr4aoj
is complete: driver 4116994 and all isolation/configure/build/install/postcheck
steps exited zero. Collect its durable records with probe_db_production.py;
do not restart this completed build. Inputs, source-before/source-after snapshots,
per-stage intent/PID/log/exit files and the private stage remain available.

The real nominated recipe creates a separate root-private db-production-*
workspace and prints its path in the recipe log. Its source bind is read-only;
only build-production is overmounted writable. Keep that work directory after
failure for diagnosis. Never resume by removing source custody or compiling into
the original fixture. A failed partial private probe is not reusable as an
accepted production package; inspect actual driver/child PIDs, source snapshots,
stage logs and exits before choosing a corrected retry. Completed native test
compilation and the running full suite do not need restarting for production
output recovery.

Actual package installation still uses the normal dispatcher after complete
suite acceptance. The independent probe invokes no package installer and its
private staging path must not be promoted directly into package success.

### Current owner-approved focused delivery continuation (ADR-0092)

The owner approved focused Berkeley DB delivery validation on 2026-11-07. This
supersedes earlier instructions to wait for a complete standard suite. Do not
restart the cancelled driver 1107192 or interpret test exit 143/driver exit 1 as
an upstream pass. Its owner-stop intent/result and original raw reports remain
under /mnt/lfs/sources/recovery/db-standard-nfv62s4o. Do not nominate that run
through the historical strict full-suite handoff.

The existing native test compilation/CuTest provenance remains verified in
/mnt/lfs/sources/recovery/db-native-m3pjqwd2 (ADR-0089); do not rebuild it merely
because the full-suite criterion changed. The focused recovery recipe
h07/berkeley-db-focused-production.sh independently revalidates that provenance,
reads a guest-root-owned mode-600 selector at
/var/log/toddy/build/h07-berkeley-db.focused-source, mounts its source read-only,
builds production in separate output, tests the staged library and then invokes
the normal package staging/install path. The selector contains the native build
generation path, not the incomplete standard fixture. Run it only via run_step.py
with h07/berkeley-db-check.sh, after verified input sync and checking real state.
The default package-manager driver now selects berkeley-db-focused.sh for clean
builds; the older complete-suite recipe and strict verifier remain optional.

Private APT generation apt-native-0vvrpixw already compiled and passed 142 unit
tests. Its final observer failed only because the real binary is under
build/ftparchive rather than build/bin. Keep that raw failed observer result;
there is no need to rerun the completed compile. Independent native consumer
checks passed using the actual executable; see H07-progress and ADR-0092.
The installed APT recipe/postcheck still must execute, including signed
repository and HTTPS checks; no private result installs or accepts a package.

Cache recovery: preserve the corrupt/interrupted cache and unpublished candidate,
remove only the rebuildable cache from the disposable target, regenerate from
original .deb inputs, reject E:/W:/BDB diagnostics even if apt-ftparchive exits
zero, validate each indexed size/SHA-256, then replace the published index.
Never delete original packages or use an unverified candidate as a signed index.

Focused installation completed: h07-berkeley-db.success.json has recipe/postcheck
exit 0; production library hash equals the private measured profile. There are
125 configured native packages. Final-base driver 22002 was launched with log
/var/log/toddy/h07-focused-final-base-launch.log and its usual
/var/log/toddy/h07-final-base-driver.{pid,exit}. Inspect actual markers/logs before
retrying. It handles APT, the owned Python alias, existing accepted ownership
steps, bootstrap quarantine and metadata closure. Do not sync inputs or start a
second dispatcher while it is active. The final verified cold pair is still the
124-package checkpoint until a new pair is actually saved and checked.

APT installed acceptance now passed after fixture-only TLS shutdown and a
SIGPIPE-safe version check (ADR-0093). The native archive/payload were reverified;
recipe/postcheck exited 0/0, zero installed payload changes. All 126 package gates
are accepted. Current final closure driver is 28080 with launch log
/var/log/toddy/h07-focused-final-closure-launch.log and standard final-base
pid/exit files. Its earlier failed exit was preserved as
/var/log/toddy/h07-focused-final-base-launch.exit. Do not repeat compilation.
Continue from actual Python-alias/quarantine/metadata/audit results; checkpoint
is still pending. See H07-focused-apt.json for actual sandbox/repository evidence.

Current closure retry is driver 39301, launch log
/var/log/toddy/h07-exact-final-closure-launch.log. Earlier numeric retry exit is
preserved in h07-numeric-final-closure-launch.exit. Exact-pin recovery passed:
GCC and Glibc-locales +toddy2 are configured against the current exact provider
revisions, with original compiler/locale payload bytes unchanged. Their failed
or earlier generations remain retained. The updater now uses provider-first
ordering, refuses baseline changes and writes generation-specific stages.
There were 43 complete current metadata receipts at the latest observation.

The deployed current closure recipe also invokes final reviewed build-directory
reconciliation before eight audits. Do not dispatch its standalone recovery
recipe while closure is active. If interrupted during directory changes, retain
its directory-ownership.intent.json and inspect every planned before/after
identity before resuming; never remove the receipt to conceal an unknown change.
Full closure acceptance, the final package export and cold paired checkpoint
remain pending. H07 must not be marked complete from the package count alone.

Final closure driver 39301 is terminal zero. All 126 metadata generations, eight
audits and Dpkg/APT consistency checks passed (H07-final-audits.json). The native
archive export completed and verified. Host checkpoint chain is now in
.local/logs/h07-final-checkpoint-run.sh, log h07-final-checkpoint.log, terminal
file h07-final-checkpoint.exit. Host shell PID 1318991 owns the sequential
clean-stop/save/verify/start/remount/check chain. Do not start the VM separately
while it runs; partial image copies without h07-final-base.json are unfinished.
On actual terminal zero, inspect the manifest and checks before accepting H07.

### Accepted H07 checkpoint; proceed with H08

H07 is accepted. .local/vm/checkpoints/h07-final-base.json records verified
builder/target hashes; both qcow2 checks passed. The cold-chain exit is 0, the
builder restarted and target kernel filesystems were remounted. Strict repeated
Dpkg audit is empty and apt-get check exits zero. See H07-checkpoint.json.
H08 is now in_progress; sync committed status/scripts before its guarded driver.
Use this cold pair if whole-target rollback is required; H06 demonstrated the
restore workflow. Never restore over an active VM or launch duplicate jobs.

### H08 accepted; H09 production build

H08 driver exited 0, native recipe/postcheck 0/0. Evidence and exact backup
location: docs/evidence/H08.md. The accepted h07-final-base cold pair remains
the pre-boot-sector recovery boundary. After committed input sync, run
`bash /opt/toddy-build/scripts/build/h09-kernel-driver.sh` detached with a
durable launch log. It captures terminal exit at
`/var/log/toddy/h09-kernel-driver.exit`; package logs are h09-kernel and
h09-boot-config under /var/log/toddy/build. It deliberately stops before
bootloader installation. Preserve any failure/source/stage before recovery;
never rerun mrproper over an unfinished or completed production build.

### H09 accepted; H10 media dependencies and assembly

The complete H09 chain exited zero. Both firmware runs and the verified cold
pair are recorded in docs/evidence/H09-native-boot.json. The builder is running
with kernel filesystems remounted. After committed input synchronization run
`bash /opt/toddy-build/scripts/build/h10-tools-driver.sh` detached. Its terminal
file is `/var/log/toddy/h10-tools-driver.exit`; each native package retains
its run_step log/marker. A failed recipe is not permission to overwrite its
source/stage; preserve it and diagnose before a targeted recovery.

ADR-0096 permits media dependency construction during H10. Release assembly
still requires H11. H10 uses assemble_root/compress_root/initramfs_archive
without --release and assemble_iso.py with --validation. The resulting media
is private validation input, not a distribution candidate. The host
`live_boot_test.py ISO MANIFEST --firmware bios --medium cdrom` uses actual
console login and retains its unique workspace under .local/vm/live-tests.
Do not start a replacement guest while its recorded container remains active.

### H10 accepted root/compression and media-only continuation

The accepted H10 root and compression are recorded in H10-root-assembly.json
and H10-root-compression.json under docs/evidence/. The initial full driver
ended 1 at the initramfs output-parent preflight; it created no initramfs.
Keep its original PID/exit/launch log. Do not rerun the full live driver over
these accepted artifacts. After synchronizing the corrected committed inputs,
run `bash /opt/toddy-build/scripts/build/h10-media-driver.sh` with a durable
launch log. It captures h10-media-driver.pid/exit under /var/log/toddy,
revalidates the source/compression bindings and creates only fresh
sources/stage/h10-live-media/{initramfs,iso}. The full clean-build driver calls
the same continuation. The original mount/ownership checks stay unchanged.

The prior failed root generations are retained under
sources/recovery/h10-info-null-20261107 and h10-runtime-path-20261107.
Their journals remain failed; separate regression evidence never relabels them.
If media generation fails after creating output, preserve its exact directory
and diagnose that stage. Never discard or rebuild an accepted compressed root
merely because an independent media step failed.

### Checkpoint retention before release-image assembly

To preserve the workstation's 100 GiB reserve, retired only the superseded
h07-native-support builder/target pair after re-reading and matching both full
retained h07-final-base and h09-boot-ready pairs against their original SHA-256.
All project qcow2 backing headers were inspected: none depends on the retired
pair. The two actual native boot overlays reference h09-boot-ready, and the
builder uses its current standalone target and the retained builder-base image.
The retired manifest and durable deletion receipt remain in the checkpoint
directory; h07-native-support is no longer a selectable restore point.

Use h07-final-base for the accepted pre-boot-sector base or h09-boot-ready for
the accepted bootable kernel/loader base. Source archives, package archives,
failed image generations, raw test evidence and all other checkpoints remain.
See docs/evidence/H11-checkpoint-retention.json for the exact retained hashes,
removed filenames and measured available space. No physical disk was touched.

### H12 native namespace follow-up profile (prepared, not yet accepted)

After H11 is completed and H12 is in_progress, the existing cold-overlay
harness accepts `python3 scripts/host/boot_test.py bios --checkpoint
h09-boot-ready --timeout 900 --regressions`. Its separate gate does not reopen
H09 or bypass the final-ISO matrix. The accepted disk image is read-only;
all writes occur in a fresh labelled test overlay. Native root/serial/QEMU,
C and Kmod guards run before any test writes.

The public regression payload selects the 48 original Glibc unsupported cases
whose preserved outputs identify namespace restrictions, adds io/tst-lchmod,
and runs Systemd test-namespace. It follows frozen Glibc Makefile's documented
`make test t=SUBDIR/TEST` target. Each process group has a timeout, original
outputs and command logs are retained, and progress.json records each completed
case. No commands from diagnostic output are executed and no host/global
security workaround is applied. Expected count is 50 total cases; an unsupported,
failed, timed-out or missing result cannot become a pass.

The guest emits checksummed compressed raw results in numbered serial chunks.
The host retains both the entire serial log and decoded native-regressions.json;
missing/conflicting/corrupt chunks fail acceptance. If the guest stops before
export, preserve its writable overlay and the reported /var/tmp workspace rather
than discarding the only raw logs. The source core-binary hashes in the native
report must also match the final-image manifest during H12 acceptance. This
cold-disk test supplies kernel/libc/Systemd follow-up evidence, not final ISO
boot, login, persistence or recovery acceptance.

### H12 USB discovery correction and recovery probes

The original release ISO failed actual USB discovery (ADR-0101). It remains at
.local/vm/live-media/h11-vtrx6uo3 and in the guest under
sources/recovery/h12-usb-discovery-20261107/h11-release-media. Its original media
driver logs are in /var/log/toddy/history/h12-usb-discovery-20261107. An initial
cross-filesystem log rename refused after relocating the media; a same-filesystem
log rename completed the recorded recovery. A premature driver correctly refused
its existing markers. No accepted root, package or compression was rebuilt.
The media-only continuation then ended zero with the revised initramfs and ISO.
Current artifact paths/hashes are in docs/evidence/H11.md.

The prepared scripts/host/live_recovery_test.py requires H11 completed and H12
in_progress and a verified final ISO/manifest. Its rescue case selects the actual
GRUB recovery menu. Its missing case boots byte-verified kernel/initramfs extracted
from that ISO without attaching any media disk. Its corrupt case flips exactly
one byte in a copied, hash-verified Squashfs extent, leaving the original intact.
All cases require a real recovery-shell command, absence of accepted-root markers,
and preserved serial logs. Only the labelled diskless test VM is stopped after
its evidence; this is not a graceful Systemd shutdown claim. Follow with normal
boot of the original verified ISO to demonstrate recovery. Native execution of
these prepared cases is still pending.

The first native namespace run retained its overlay at
.local/vm/boot-tests/h09-bios-m2gayrqx. Systemd test-namespace exited zero. Glibc's
make test convenience target tried implicit rebuilds against its old bootstrap
ar path, so those executions are failed, not passing native regressions. The
serial export also missed chunk 67/112; the guest's exact complete report remains
at /var/tmp/toddy-native-regressions-vzwqsj8n/result.json in that overlay. Preserve
it for independent recovery; do not trust partial decoded text as acceptance.
