# Development recovery

Current checkpoint: H06 native chroot, eight temporary packages, /tools removal and real paired-disk restoration passed. Target root is /dev/vdb4 mounted at /mnt/lfs.
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

## Latest verified checkpoint and next action

H06 passed: ten recipe/postcheck successes, native C/C++ and post-cleanup
self-hosting tests, plus actual checkpoint restoration. Latest verified pair
and hash manifest: .local/vm/checkpoints/h06-ready.json, h06-ready-builder.qcow2
and h06-ready-target.qcow2. The modified pre-restore pair is preserved; see
.local/vm/last-restore.json for its exact directory. No /tools remains.

The guest is running and pseudo filesystems are mounted. After any restart:

```sh
python3 scripts/host/vm.py ssh 'bash /opt/toddy-build/scripts/build/mount-kernfs.sh'
python3 scripts/host/vm.py ssh 'bash /opt/toddy-build/scripts/build/h06/cleanup-check.sh'
```

H07 is next: use frozen chapter 8 order, stage final packages, check ownership
before native .deb installation, and retain critical test results. Man-pages and iana-etc have passed; ownership rejection probe also passed.
Final Glibc critical suite and native installation passed with one explicitly
documented chroot failure; locales, tzdata, Zlib, Bzip2 and Xz also passed.
Next is Lz4 in frozen chapter 8 order, then the remaining final base.
Preserve h06-ready before final libc changes. Security
overlay research is recorded separately; no fix is claimed built yet.

Never rerun the account-creation bootstrap over existing work. Resume mount
state with mount-kernfs.sh. Never run chroot recipe bodies on builder root or
workstation. Check failed/running manifests before retrying a package.

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
