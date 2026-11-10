# Phase 2 continuation card

Owner boundary: **complete ALL B02, then stop before another story**. Full Phase2
Goal incomplete. B01/B03 accepted; B02 in_progress; B04 integration blocked;
B05–B13/G2 pending. Weighted accepted Phase2 progress13%, no partial B02 percentage.
ADR0113 records authorization. Physical foundation tests unperformed. No accepted
complete GNOME/login/basic apps or Phase2 ISO exists.

## Current slice and exact next action

Private Linux7.1.8 Landlock candidate COMPILED and diagnostic BIOS/UEFI BOOTED;
NOT INSTALLED or accepted as installed Systemd/desktop.
[Compile evidence](evidence/B02-kernel-landlock-compile.json), ADR0201.
Actual build4PID19120 terminal0, incremental compiler15.003s; complete worker
21.871s includes source verification. Config delta exactly SECURITY_LANDLOCK n→y
and its selected SECURITY_PATH n→y; release7.1.8-toddy/source/toolchain unchanged.
Original cache111558entries/2599875499bytes fully byte/metadata identical after
compile,93715pristine source entries unchanged in original and private view.
Candidate bzImageSHA18c4d9e6a64554296d8e9a037c2383e7426a0cf155b6d757d0693fce0d087ad1;
rawSHAa946b14b08bc3703aac69fc717a6a461f77690d635087d6555c049ca4ba915da.
No active guest writer. Installed linux-kernel7.1.8-1/boot files unchanged.

Native diagnostic prepare1PID21249 actual0, static native libc/UID101; fixture
kernel-landlock-1/boot-probe-1/prepared.json. Original input C source immutable at
inputs/linux-landlock-7.1.8/toddy-landlock-init.c; token and source hash recorded
in /var/log/toddy/phase2/kernel-landlock-boot-input-1.json. InitramfsSHA
388c307ed47f5e5d47ca16c4de0f95458232ead63a51fc19d20e50a699856b19.
Native diagnostic1 COMPLETE, actual BIOS+UEFI exits0/OOMfalse, no disks/network.
Both ABI9/UID101:2rulesets/4allowed roundtrips/4denied reads/4denied writes/
4denied creates/2fresh-process recoveries/2seccomp denials, namespace0 and actual
native dummy module insert/remove0. Both containers terminal/removed, parent
builder unchanged, no restoration needed. [Native proof](evidence/B02-kernel-landlock-native.json).
RawSHAfebffec05ffb7abdbe70cba304d02503db4db85edbcb427bf614f1c6c133b61b.
All20 original owned .ko payload files are byte-identical to candidate modules;
this supports retaining original module bytes and kernelrelease for recovery,
but no installed rollback/boot-entry acceptance is claimed yet.
NEVER replay native-kernel-landlock-1 or its preparation. Actual host folder
.local/phase2/native-kernel-landlock-1, complete result.json/driver.exit0/serials.
Kernel stage2PID22487 actual0, [proof](evidence/B02-kernel-landlock-stage.json).
Authenticated original archive27d735... reused/all12023payload entries verified;
all20module bytes unchanged. Three candidate image/config/System.map files plus
three original -foundation rollback copies and README. Stage regular files11261;
free240488448B before manifest output. RawSHAea67c110d0afcadb36c7b2ac2c84df61f420611ce4680718409ca0cb9125352f.
Stage1PID22058 own .ko modules.order assumption failed before backups/manifest;
actual source lists20 .o objects. Stage2 maps ONLY final .o→.ko/exact20set and
reuses extraction; no archive extraction/compiler/native diagnostic replay.
NEVER replay stage1/2 or original extraction. Current stage
/mnt/lfs/sources/phase2/work/kernel-landlock-1/stage and kernel-stage-1.json.
No native package/boot config/installed Systemd change. Future native promotion
must avoid an unnecessary duplicate full stage on target root: use controlled
bind of verified scratch stage under /mnt/lfs/sources/stage with unchanged full
root transaction checks, stage ownership normalization/provenance. Measure actual
archive/cache/installed backup space before committing; preserve reserves.
Boot config owner is toddy-boot-config, /etc/toddy/grub.cfg conffile with
/boot/grub/grub.cfg→../../etc/toddy/grub.cfg; do not cross kernel package ownership.
Next implement qualifier/native package revision and separate owned recovery
entry, then actual installed-system and rollback boot checks.

EXACT NEXT: read install_verified_stage.py/stage_package.py and current H09
boot ownership/config contract; prepare verified stage of current candidate
with owned original kernel image/config/System.map retained as rollback artifacts.
Use native package revision (same source/release, unchanged20modules), preserve
old archive, qualify generated boot-entry ownership and actual rollback path;
no foundation rebuild or source/config/compiler/native diagnostic replay.
Installed linux-kernel7.1.8-1 remains untouched. After kernel native delivery,
LocalSearch3.11.1 then Nautilus. Complete ALL B02 then stop.

## Preserved failures and resource postconditions

Config jobs1PID3557/2PID4897 terminal1 before compiler: newly installed B02 Rust
was auto-detected by init/Kconfig even without selected kernel Rust. Env-only
RUSTC=false was overridden by Makefile `RUSTC = rustc`. Second correction uses
explicit `make RUSTC=false`; exact two-symbol gate passed. Cause resolved; retain
both failures, no retry/reset of their ledger budget.

Build3PID6236 terminal1/make-2: reserve monitor safely interrupted final vmlinux
link at219.049s/min131653632B. No package/boot write. One bounded fixed virtual
scratch growth768MiB→1GiB (no reformat), same inode/UUID; host after complete
allocation107687411712B >100GiB. QMP/guest geometry update released ~4.5MiB physical
extent; existing-size fallocate restored full allocation without replaying resize.
Host receipt .local/vm/phase2/kernel-landlock-growth.json state filesystem-grown,
allocation_reconciled=true; guest kernel-landlock-resize-1.json complete.

Build4 reused partial3, no config/olddefconfig/source replay. Historical monitor
observed152457216B minimum while polling but late final link ended at88567808B.
Do NOT treat the poll-only minimum as final reserve proof. Canonical monitor now
records final free explicitly. After terminal0/full original-cache proof, guarded
retirement1 removed ONLY five named private .tmp_vmlinux* intermediates; manifests
retained/final artifacts unchanged/free388354048B. Receipt
kernel-landlock-temporary-retirement-1.json complete. NEVER replay retirement.
No fresh whole-source rebuild/reproducibility acceptance is claimed.

## Actual builder, mounts and recovery

Current boot3a77a52a-5994-4f9c-9a57-d8582921275c; target
/mnt/lfs=/dev/vdb4/TODDY-LFS-TARGET (filesystem labelTODDY_LFS). One writer via
/var/log/toddy/build/build.lock. Target16GiB/host100GiB/scratch128MiB reserves.
Current kernel scratch fixed /dev/disk/by-id/virtio-TODDY-B02-KERNEL→/dev/vdc,
1GiB ext4 UUIDc6c4176d-faed-4ee3-9ae0-94914a0af666 mounted nosuid/nodev at
/mnt/lfs/sources/phase2/work/kernel-landlock-1. DO NOT format/grow/restart/reprepare.

Real COW preparation1 complete: work/private-overlay root0700 contains readonly
lower bind/upper/work; work/merged is overlay metacopy=on,index=off, rootUID101.
Input /mnt/lfs/sources/phase2/inputs/linux-landlock-7.1.8. Exact isolation branch
exposes only merged writable and original readonly at /src/cache; upper internals
inaccessible. Isolation1PID3069 actual0: no caps/NNP, source+/usr write denial,
package DB absent/private write-read-remove/source unchanged. Baseline.jsonSHA
d0e66e8e3cc2260d35242a1dca634e72bfd6bcd3d63a5bd94bac591a173114bf immutable.
No baseline rehash/recomputation with unchanged inputs. Original source inode7523763.

Existing six scratch/Systemd source/companion restored after controlled restart:
kernel-scratch-builder-restore-1.json and glycin-gtk4-work-restored-kernel-1.json
COMPLETE; never replay. On a FUTURE cold restart first inspect actual disk/UUID/
mounts and terminal jobs. Restore ONLY existing six via restore_volumes() (not
virtual_discard_checkpoint.main/trim), same Systemd source via --restore, new
receipt names, then same Glycin companion. Kernel scratch requires mounting SAME
UUID (no mkfs) and restoring its existing private readonly lower/overlay (no
preparation/chown replay); no cold restoration for this new COW profile has been
performed yet. Native diagnostic above does NOT stop parent or share its disks.

Systemd source inode8930333/input7547189,7193files/SHA
2a683ffe0cdab7349a4b2b64b932fab647baaab4e7ab5b7c64520ff3443c5667.
Glycin parent UUID1ae14c30-65f3-4e02-be0a-b257719455f2, companion backing inode5538,
underlying mountpoint9503173. GTK custody1 complete/eight real restores; do not
replay or reuse retired stages. New stock schema cache needs fresh current owned
archive extraction. Preserve full checkpoint/final-image integrity.

## Accepted predecessors and parked graphical work

GExiv20.16.2, Exiv20.28.8, Brotli1.2,INIh62, Blueprint0.22.2, Tinysparql3.11.1,
GlycinGTK4 and earlier terminal/media/session dependencies owned. Exact scope,
source/archive/raw identities and failures in [B02 evidence](evidence/B02.md) and
story/status. Never rebuild/reinstall/retest unchanged accepted slices. Terminal
stock shared schema integration and real app GUI remain pending. Nautilus needs
real LocalSearch executable even for headless configuration and for app launch;
do not bypass it or disable Landlock/seccomp. Optional catalogue candidates are
not mandatory accepted apps.

shell-first-native-session has two failed corrections; no unchanged headless
retry. Native1 no actions; native2 diagnostic1280x720 screenshot/PAM-logind-userbus
cleanup0/no actions; native3 partial GTK mapping/focusfalse/incomplete UART report
(missing50of76). NO positive GUI acceptance. ADR0184/0186/0187 and evidence retain
failures. Concrete unblock actual virtual seat/input or new source-backed cause
with complete reliable evidence. No fake focus/events/unsafe-mode/weakened hashes.
Persistent .local/phase2/failures.json budgets survive compaction.

Last published19723d195ccbd4a7c5c89bdd0bca8cba10835e13: all3CI success,
exact publicHTTP200/indexSHA
5749b37fd1ab270e2b29fcfb2dde1625ac5f1fa4467b854dacd72345cca519cf.
