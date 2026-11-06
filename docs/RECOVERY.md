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

Latest paired offline checkpoint: .local/vm/checkpoints/h03-builder.qcow2 and
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
Berkeley DB complete Tcl suite is running after successful C tests. Test-only
DBM/compat185 and static object generation satisfy actual upstream test/symbol
requirements; production still omits DBM/compat185 and stages no .a/.la files.
Inspect /sources/db-5.3.28/build-test/ALL.OUT for live progress, not only tee tail.
Prepared native Perl/Triehash/Which/Libseccomp/APT recipes are not yet accepted.
Once dispatcher is quiescent, sync then run h07-perl-test-tools-driver.sh; it
uses accepted native Dpkg backend and must pass real package postconditions. Native APT, packaging
backend transition, ownership/dependency/conffile/license closure remain pending.

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
