# Native dosfstools4.2 prerequisite

Source preparation only: no compilation, mkfs/fsck execution, disk operation or
VM write was performed to prepare these recipes. The coordinator remains the
single guest/package writer. Source/signature verification, the frozen source
lock and component-license/package metadata are parent-owned prerequisites.
This recipe never fetches keys or sources or changes a version.

The source follows frozen BLFS13.1-systemd `postlfs/dosfstools.html`, inspected
locally. Archive `dosfstools-4.2.tar.gz` is320,917bytes, SHA256
`64926eebf90092dca21b14259a5301b7b98e7b1943e8a201c7d726084809b527`,
BLFS MD5 `49c8e457327dc61efab5b115a27b087a`. The exact archive has157members,
1,356,148expanded regular-file bytes and no links. The parent must add the real
`source_verified` row after its actual upstream verification, not merely set a
flag to satisfy this preparer. Retain the original GPL notices and per-file
conditions; generic named notices and copyright consolidation use existing
helpers. An extra source-header notice policy, if needed, belongs in the parent's
license metadata, not a flattened substitute license in this recipe.

## Exact single-writer commands

Deliver the committed recipes/helpers through the existing verified metadata
route. All commands below run only in the guarded disposable native builder.
Do not overlap another compile or package writer. Reconcile actual prior state
before any command; existing prepare/job/qualify/install state refuses replay.

```sh
bash /opt/toddy-build/scripts/build/phase2/dosfstools-prepare.sh
python3 /opt/toddy-build/scripts/build/phase2/job.py \
  dosfstools-1 \
  /mnt/lfs/sources/phase2/inputs/dosfstools-4.2-1 \
  /mnt/lfs/sources/phase2/work/dosfstools-1 \
  bash /src/toddy-build.sh
bash /opt/toddy-build/scripts/build/phase2/dosfstools-qualify.sh
python3 /opt/toddy-build/scripts/build/run_step.py \
  b12-dosfstools-install-1 \
  /opt/toddy-build/scripts/build/phase2/dosfstools-install.sh \
  /opt/toddy-build/scripts/build/phase2/dosfstools-check.sh --user root
```

The check wrapper is the exact independent installed postcondition of that
`run_step` transaction. It is not a command to replay after clearing a marker.
No extra isolation profile or build framework is added. Direct-script helper
imports resolve their fixed phase2/build parents, including under Python `-I`.

Preparation validates the archive, frozen row, actual native tester UID/GID101,
existing source-built glibc/vim archives/records, and the exact owned native xxd.
It preserves at least16GiB target free plus512MiB scratch allowance. It records
intent before extraction, mounts a NEW root-owned source read-only and verifies
actual root EROFS denial, then creates the UID101 work directory. Recipe, helper,
job/harness, dependency/archive and boot/input inode pins survive between phases.

The existing qualified `isolated.sh` gives UID101 read-only native `/usr` and
`/src`, a private writable `/build`/`/stage`/tmp and no general guest filesystem,
keys or external network. A writable build copy preserves upstream's in-tree
fixture layout: `test-fsck` reads relative `.args`, which a blind VPATH build
would omit. Configure uses `/usr`, `/usr/sbin`, native compatibility symlinks,
`/usr/share/man` and `/usr/share/doc/dosfstools-4.2`. Compilation uses4jobs; the
original suite runs serially. No source test is disabled or rewritten.

The frozen upstream suite contains40tests. `xxd` is REQUIRED before configure,
and the configured tests Makefile must say `XXD_FOUND = yes`. Every `.trs` must
exist with exactly39PASS plus the sole upstream-declared
`check-huge.fsck` XFAIL. SKIP, FAIL, ERROR, XPASS, missing/extra results or a nonzero
`make check` exit block staging qualification. Upstream's existing XFAIL remains
visible; it is not reported as40passing tests. Original logs/results are retained.

The staged and installed consumers each create a NEW128MiB regular sparse file
as UID101. They hold its O_EXCL/O_NOFOLLOW descriptor and pass only that verified
regular FD to native mkfs.fat/fsck.fat/fatlabel; no raw/loop device, partition,
mount, supplied image path or real host disk is accepted. The probe checks FAT32
BPB/label/geometry, FSInfo, backup boot, sparse allocation and exact label readback,
and requires fsck `-n`/label reads to leave the whole image hash unchanged. The
build probe image stays under work; the installed probe's private temporary home
is removed. This verifies FAT tools on a file, not installer disk/boot acceptance.

Qualification rechecks actual isolated job/command/harness exits, all40original
results, the exact stage manifest, legal COPYING bytes, required regular sbin
ELFs, exact relative compatibility links and installed native glibc providers.
`readelf` must report AMD64 dynamic binaries, no runtime search paths, the native
loader and only declared/owned providers with exact bytes. An unexpected external
library blocks promotion before package writes; do not silently broaden Depends.

The standard full-root `run_step` journal is mandatory for this first native
write. It owns the existing global lock; install/check do not reacquire it.
Dependencies and16GiB+scratch+payload/archive allowance are checked again. The
existing packager creates `dosfstools_4.2-1+toddy1_amd64.deb`, retains authenticated
source/legal notices, detects ownership conflicts and performs controlled dpkg
installation. `/usr/sbin/mkfs.fat` matches the existing LinuxDisk fixed tool path.

The checker uses a private dev/proc mount namespace, verifies native configured
version, pinned source/archive/recipe/record, all installed regular bytes/modes/
UID/GID and exact link/ownership state, runs the UID101 installed regular-file
consumer, `dpkg --audit`, `apt-get check` and the reserve check. Keep all
`dosfstools-*` receipts/logs under `/var/log/toddy/phase2`, both native archive and
record, and the full `b12-dosfstools-install-1.*` journal. Inspect its complete
changed paths; a successful stage alone is not a native package audit.

On interruption inspect job `.exit`, actual recipe markers, dpkg state and file
postconditions before deciding on a NEW attempt. Never replay a format, clear an
uncertain writer marker, substitute a host binary or accept skipped upstream
results. Actual installer/Calamares qualification resumes separately after this
native dependency transaction passes. Foundation evidence and existing package
recipes remain unchanged.

Focused source checks (no mkfs/compile/VM execution):

```sh
python3 -m unittest discover -s tests -p test_dosfstools_native.py -v
```
