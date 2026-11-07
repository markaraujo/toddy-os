# Current build procedure

H01–H06 are validated; H07 final-base implementation is in progress with 124
accepted native packages, including native Dpkg, Perl support, Triehash and
Which/Libseccomp/Tcsh and API/layout/build-support ownership. The corrected
complete Berkeley DB Tcl rerun and APT/final closure remain pending. This remains a partial build manual; no Toddy ISO exists.
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
historical input hashes. For the final GCC job, a sidecar
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

Post-compiler recipes through Bash follow frozen LFS 13.1-systemd 8.33–8.39
and passed their target checks, with qualified raw suite differences retained
in the evidence/ADRs. Their driver refuses to start
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

Final GCC installation is separately gated by evaluate-gcc.py and the pinned
compiler-test-reference.json. Require all six merged reports, complete declared
pass counts at least as large as the official reference, and only exact known
unexpected-status lines from that same hash-pinned LFS run. New FAIL/XPASS/
UNRESOLVED/ERROR cases remain rejected. The source-generated report script is
data only. GCC's raw make exit alone is not acceptance. Preserve raw parallel
.sum.sep/.log.sep files alongside the merged reports before cleaning source.

ADR-0014 separates gcc-runtime ownership from compiler/development files.
Native compiler/runtime installation and C/C++ thread/loader checks passed
after critical acceptance. Existing native C++ consumers' dependency
metadata remains subject to the final audit; this is not yet a closed graph.

Before a fresh full build sync, fetch the pinned compiler reference:

```sh
python3 scripts/fetch_compiler_reference.py
python3 scripts/host/sync_build.py
```

The sync refuses unfinished running markers, verifies the content-addressed
reference cache and copies the reference as data into target evidence. The
future GCC build wrapper preflights it before spending time compiling. This
preflight was added after the completed first suite; the original first-run
recipe hashes/sidecar remain preserved in its recorded commit history.


## Current final-base continuation

Inspect the live dispatcher, success/failed/running markers and ALL.OUT before
acting; do not dispatch concurrently or sync while Berkeley DB holds the lock.
After actual success and a quiescent boundary:

```sh
python3 scripts/host/sync_build.py
python3 scripts/host/vm.py ssh 'nohup bash /opt/toddy-build/scripts/build/h07-perl-test-tools-driver.sh > /var/log/toddy/h07-perl-test-tools-driver.log 2>&1 < /dev/null & echo $!'
```

Inspect the complete support-driver result and per-package postchecks. Only its
success permits h07-final-base-driver.sh (APT, alias/ACL, ownership/quarantine,
metadata closure). Native APT repository/upgrade integrity and final closure
remain pending. See docs/RECOVERY.md for exact retained checkpoints and commands.
Native build integration, backend archive-only and DBus XML bounds probes are
supplemental evidence; they do not replace full recipe/postcheck acceptance.


Berkeley DB test-process prerequisite (ADR-0068): the frozen upstream archive
omits the helper used by eleven multi-process Tcl cases. The project supplies a
native C adapter in scripts/build/h07/db_repsite.c, built only in build-test by
berkeley-db-test-helper.sh. Its pinned implementation passed all eleven unchanged
upstream cases in a private native fixture; it is excluded from production.
Fresh and verified recovery builds include it and the two frozen test-fixture
patches. Complete standard-suite success is still required before production
packaging. Input preflight is reproducible with
python3 scripts/host/probe_db_test_fixtures.py after fetching frozen sources.


Optional H07 parallel test recovery is documented in ADR-0069. A physical
private copy of the verified native build and corrected frozen Tcl inputs is
mapped to the canonical source path only inside private PID/IPC/network/mount
namespaces. The versioned isolated driver runs CuTest and the complete unchanged
run_std with strict failure handling and protected input/report hashes. It does
not install a package. This optimization does not combine partial old results
or reduce the standard suite. The normal fresh-build recipe remains the default
reproduction path; production consumption of the isolated complete result still
requires a separately validated handoff and native package postchecks.

The final staged image's private-key armor review is prepared in
scripts/build/h11/review_image_key_markers.py (ADR-0071). After the actual H11
gate and optional QA removal, run it against the designated fresh image root:

```sh
python3 -B /opt/toddy-build/scripts/build/h11/review_image_key_markers.py /mnt/lfs/sources/stage/RELEASE_ROOT
```

Replace RELEASE_ROOT with the actual completed staging generation; do not point
it at the installed builder. Preserve the complete JSON report outside the image.
The command exits nonzero for unresolved armor findings or unread special nodes.
It retains all raw findings, including exact source/package/parser-qualified
OpenSSL manual examples. Its success covers only that narrow marker check;
the separate full credential, identity, payload and release gates still apply.


Fresh uncompressed root assembly is prepared in h10/assemble_root.py (ADR-0072).
After H09 acceptance, H10 in progress and actual native Squashfs tool acceptance,
invoke the standalone CLI in the guarded builder:

```sh
python3 -B /opt/toddy-build/scripts/build/h10/assemble_root.py /mnt/lfs/sources/stage/h10-live-root /mnt/lfs/sources/stage/h10-live-root-evidence
```

Both destinations must be absent. This CLI owns build.lock; do not wrap it in
run_step.py. It preserves each component report and a durable assembly journal
outside the image. After H10 acceptance and H11's actual Python ownership
transfer, refresh a separate release generation using --release and two new
paths. The prepared CLI checks owned/generated attribution; dependency closure,
complete credential/license, compression/initramfs and actual boot checks remain
required after root assembly. Current native
probes verify component behavior and readiness refusal; full positive assembly
has not run. Never change the gates to exercise it early.


ADR-0073 adds a separate whole-tree attribution step to the prepared assembler.
Keep the verified copy input-manifest.json, image-attribution-plan and comparison
report together with the final image manifest. Every package/generated path must
match its declared bytes, metadata and origin; unknown state is a failure. This
also checks source xattrs and remaining hardlink groups. The comparison does not
replace arbitrary-secret, dependency, license or actual boot acceptance.
