# Current build procedure

This document covers verified H01–H03 and the running H04 implementation.
It is not a complete release build manual yet. No Toddy ISO exists.
Use status.json and the evidence files to distinguish passed milestones from
recipes still under validation. All commands below run from the checkout root.

## Workstation requirements

Linux x86_64, working Docker and access to /dev/kvm, Python 3.12+ (tar data
filter and hashlib.file_digest), OpenSSH client, curl, tar and Git. The QEMU
container installs tools from Ubuntu's trusted package archive and records its
package list. Host package installation is unnecessary on the measured host.
Do not mount the Docker socket or physical block devices into a guest.

```sh
scripts/host/inventory.sh
docker build -t toddy-qemu:h01 -f scripts/host/Dockerfile .
python3 scripts/host/fetch_image.py
python3 scripts/host/vm.py prepare
python3 scripts/host/vm.py start
```

Wait for actual guest SSH and cloud-init completion, inspecting the serial log
if unavailable. The start command only launches QEMU; it does not assert boot
success. Review image hash, disk identity and guest hostname before continuing.

```sh
python3 scripts/host/vm.py ssh 'hostname; cloud-init status; lsblk -o NAME,SIZE,SERIAL,MOUNTPOINTS'
python3 scripts/host/vm.py ssh 'bash -s' < scripts/host/guest-setup.sh
python3 scripts/host/check_requirements.py
python3 scripts/fetch_books.py
python3 scripts/fetch_sources.py
python3 scripts/fetch_security_overlay.py
```

Fetched books are in .local/books/lfs/13.1 and .local/books/blfs. Consult the
specific frozen section before each recipe. Review security obligations in
ADR-0007. All sources are verified before extraction; do not use a moving
stable book or substitute package versions without a recorded decision.

## First target preparation

Only this designated VM's blank disk with serial TODDY-LFS-TARGET may be
partitioned. The script validates target identity before any write and aborts
if an unknown filesystem exists. --apply is destructive to that disposable
virtual disk and is authorized for this build; it never runs on physical host
devices. Run the dry plan first and inspect it.

```sh
python3 scripts/host/vm.py ssh 'mkdir -p /opt/toddy-build'
tar -cf - scripts/build config/books.lock.json config/sources.lock.json | python3 scripts/host/vm.py ssh 'tar --no-overwrite-dir -xf - -C /opt/toddy-build'
python3 scripts/host/vm.py ssh 'bash /opt/toddy-build/scripts/build/prepare-target.sh'
python3 scripts/host/vm.py ssh 'bash /opt/toddy-build/scripts/build/prepare-target.sh --apply'
python3 scripts/host/sync_build.py
python3 scripts/host/vm.py ssh 'bash /opt/toddy-build/scripts/build/package-prototype.sh'
```

The runner probe scripts are one-time disposable tests, with fixed step names;
inspect existing marker files before intentional reruns. The source transfer
must preserve the sticky sources directory mode: never transfer a whole
cache directory with metadata overwriting /mnt/lfs/sources.

## H04 cross-toolchain

Recipes follow LFS 13.1-systemd chapter 5 exactly, with integrity verification,
logs, install manifests and explicit postconditions added around the commands.
The eight-job setting is for this build guest, not an architecture tuning flag.
No final compiler/libc test is waived by this temporary build.

```sh
python3 scripts/host/vm.py ssh 'nohup bash /opt/toddy-build/scripts/build/h04-driver.sh > /var/log/toddy/h04-driver.log 2>&1 < /dev/null & echo $! > /var/log/toddy/h04-driver.pid'
python3 scripts/host/vm.py ssh 'cat /var/log/toddy/h04-driver.log; ls /var/log/toddy/build/'
```

Do not launch a second driver while one is running. Inspect the recorded PID
and child processes, driver exit file, each recipe and postcheck result and
manifest before continuing. Exit 0 plus verified postconditions is required;
no exit file or a running marker means unfinished work. Logs survive SSH exit.
On failure, inspect logs and partial target changes before retry; the runner
preserves failed attempts under history/. For interrupted running markers,
archive the record only after diagnosing and recovering partial installation.

## Recovery

See [recovery checkpoints](RECOVERY.md). Stop QEMU cleanly before copying or
restoring images. Keep source archives, images and logs outside Git. Full
rebuild reproducibility and final package/license inventories remain release
acceptance work; the current tooling does not claim byte-identical results.

## H05 temporary tools

After H04 passes, scripts/build/h05-driver.sh builds the chapter 6 sequence.
Its recipe command blocks were extracted deterministically from the pinned
book with scripts/derive_temporary_recipes.py, then reviewed. Added wrappers
verify sources, save logs/configure evidence and check installed target ELF
binaries using the target loader; original instruction license is retained.
The native pass-2 compiler is reserved for actual chroot execution in H06.

```sh
python3 scripts/host/vm.py ssh 'nohup bash /opt/toddy-build/scripts/build/h05-driver.sh > /var/log/toddy/h05-driver.log 2>&1 < /dev/null & echo $! > /var/log/toddy/h05-driver.pid'
```

Prerequisites are checked again by the driver. Inspect exit/record files
before continuing. Do not regenerate or edit running recipes without a
specific diagnosed correction and a recorded recovery point.

## H06 native chroot

Only after all H05 records pass, use scripts/build/h06-driver.sh. It verifies
the intended mounted virtual disk, changes temporary payload ownership to
root, mounts guest dev/proc/sys/run/devpts and builds eight additional tools
inside an empty-environment chroot. The interactive book shell re-exec is
adapted to separate clean noninteractive shells. Native C/C++ compile/run is
checked before proceeding. No tool is installed into the builder's root.

```sh
python3 scripts/host/vm.py ssh 'nohup bash /opt/toddy-build/scripts/build/h06-driver.sh > /var/log/toddy/h06-driver.log 2>&1 < /dev/null & echo $! > /var/log/toddy/h06-driver.pid'
```

The cleanup removes /tools and verifies self-hosted C execution afterward.
Checkpoint restoration remains a separate required H06 acceptance experiment;
a driver exit alone does not complete the milestone.

## Verified disk-pair checkpoints

Use scripts/host/checkpoint.py only with QEMU stopped. It refuses a live VM,
checks qcow2 consistency, hashes the copied disks and records their backing
image hash. Restoring preserves the current pair before replacing anything;
an interrupted restoration blocks VM startup until the same restore finishes.

```sh
python3 scripts/host/vm.py stop
python3 scripts/host/checkpoint.py save example-checkpoint
python3 scripts/host/checkpoint.py verify example-checkpoint
python3 scripts/host/vm.py start
```

To recover an existing named checkpoint, stop the VM, run checkpoint.py restore
with that name, then restart and verify guest postconditions. Never restore
images beneath a running process. The checkpoint storage is local to the same
physical disk; external disaster backup is a separate release requirement.

## Final Glibc critical suite and native package

ADR-0009 selects the pinned stable security patch without changing Glibc 2.44.
Fetch additions with python3 scripts/fetch_security_overlay.py. Baseline inputs
stay intact. h07-glibc-build compiles and runs the full critical make check
suite before installation. Raw exit code, original tests.sum and per-test
outputs are retained at target /sources/evidence/h07-glibc/. Its classifier
rejects incomplete evidence, unexplained failures and interrupted runs.

Only after that build/postcheck succeeds may h07-glibc-install stage the
payload, preserve copyright notices, preflight ownership, build/install the
native .deb and validate actual C execution. Locales (book minimum plus
pt_BR.UTF-8) and tzdata are separate tracked packages. Derived ld.so.cache is
regenerated after installation. Remaining critical compiler/binutils tests
are separate mandatory H07 work.

Native H07 test tools follow frozen LFS 13.1-systemd sections 8.14–8.21.
Detached recipes reset inherited ignored HUP/INT/QUIT/TERM before Bash;
new process groups alone do not restore signal dispositions. Preserve raw
suite results and distinguish skipped tests from actual passes. The final
Binutils 2.47 suite runs before installation and retains its original exit
and every .sum/.log report. For final GMP, use the book-supported
--host=none-linux-gnu to avoid optimizing the distributed library solely for
the builder's Ryzen CPU; retain the mandatory full tests and >=199 PASS check.
This does not yet establish a tested release CPU/hardware baseline.

Build provenance now records the complete supporting .sh/.py recipe set,
including inner scripts streamed into chroot, with per-file SHA-256 and a
canonical set hash. Native archive records retain the same set. This extends
the original outer recipe/runner/source hashes; it does not invent missing
historical input hashes. For the already-running final GCC job, a sidecar
/var/log/toddy/build/h07-gcc-build.recipe-set.json was captured during build,
with matching original runner/outer hashes and source commit 3489a9b.
The critical GCC scripts were unchanged; the later runner instrumentation
applies to subsequent steps. Preserve both original record and sidecar.

Export a verified partial native inventory in the running builder:

```sh
python3 scripts/host/vm.py ssh 'python3 /opt/toddy-build/scripts/build/export_inventory.py' > .local/inventories/native-partial.json
```

This read-only export checks installed version records, every native .deb,
corresponding source SHA-256 and installed copyright notices. Its first real
run verified 31 packages. It explicitly reports incomplete release scope,
pending dependency/license review and missing early supporting-recipe hashes;
it does not convert historical gaps into claimed verification.

Additional package-manager source archives (ADR-0012) can be fetched/verified:

```sh
python3 scripts/fetch_security_overlay.py --supplemental
```

sync_build.py includes the supplemental lock and verifies the pinned archives
before transferring. Native source.py accepts only frozen listed additions;
no new source/component is extracted solely because a URL was supplied.

Post-compiler recipes through Bash are prepared from frozen LFS 13.1-systemd
8.33–8.39 but are not yet target-validated. Their driver refuses to start
without h07-gcc-install.success.json. Ncurses includes an upstream automatic
setupterm example matrix after installation plus native screen/terminfo
checks; interactive examples are not represented as an exhaustive suite.
Bash tests use the required tester-owned Expect PTY. Its upstream run-all
always exits zero, so an independent evaluator requires every expected test
header and rejects diff output before staging. Any legitimate documented
exception still needs actual source-backed classification after observation.
Two additional Bash test locales are staged with --no-archive in a separate
native package to preserve glibc-locales ownership; only the explicit ascii
compatibility warning for these legacy encodings is suppressed, not errors.
