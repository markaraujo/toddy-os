# Phase 2 continuation card

## Read-only restart reconciliation (2026-11-18)

Git is clean at 02b4981 before this environment correction. No guest writer is
running. The stopped `toddy-phase2-candidate` Docker record exited 0 and was
removed after its identity, label and mounts were checked; the Candidate qcow2
files, accepted backings, serial log and private runtime pointer were preserved.
Both Candidate overlays and all five backings passed read-only `qemu-img check`.
This verifies qcow2 structure, not guest filesystem contents or image acceptance.

Read-only libguestfs inspection identified the builder's `/usr/sbin/chroot` and
the installed `resource_recipe.py` SHA-256
`b1395671ad0c8b68f9b0edc81ee1980f55ec7937d3f6b7bcca87ca0505d2272a`,
matching current source. The older `/usr/bin/chroot` ENOENT log predates the
`bc27eba` correction. The target ext4 UUID
`e7726c1a-8f91-445f-96ac-88721b58caf8` matches the builder's `/mnt/lfs`
fstab entry. Its root at `/sources/stage/toddy-mvp-live-image-1/root` retains
inode 11337797 and the pinned unpack/resource intents. The later
`resource-account-recovery-intent2.json` exists, but no candidate resource
receipt exists. The subsequent log records `dconf update` returning nonzero.
Its `/etc/dconf/db/toddy-desktop` output was modified at 21:14:44 on 2026-11-16
and matches the declared SHA-256
`5d86fa8e8e16c157ec30cc9e2cca4fe71d50b580d1932936894b927036100cb4`.
The command's stderr was suppressed, so its failure cause remains unknown and
the partially changed root is not qualified. Never replay any of the three
resource intents or run another native producer in this root. Source now scopes
this producer to `dconf compile /etc/dconf/db/toddy-desktop
/etc/dconf/db/toddy-desktop.d`, avoiding unrelated databases. The next
development slice must sync that reviewed source through the controlled guest
path, verify its expected output in an isolated disposable root, preserve this
failed root, then plan a distinct fresh candidate generation. Stop after one
failed isolated probe; an unchanged retry is not justified by this evidence.

The target ext4 had 30.45 GiB available, above its unchanged 16 GiB reserve.
The host had about 92 GiB available, below the default Candidate 100 GiB +
512 MiB start floor but above ADR-0251's 60 GiB + 512 MiB delivery floor.
`phase2_candidate_vm.py --mvp-delivery start` now selects that temporary floor
explicitly for this MVP candidate only; ordinary starts and preparation keep
their default floor. Recheck actual free space before starting. The first
start after this source change requires a clean committed checkout and the
existing single-writer/backing guards. Do not infer B06, ISO or G2 acceptance.

## Immediate owner UI delivery

Owner explicitly approved a temporary60GiB+512MiB host reserve for this delivery
([ADR-0251](adr/0251-owner-allows-temporary-mvp-host-reserve.md)). The16GiB guest
reserve and preservation of personal data/recovery images remain unchanged.
Older100GiB references below remain historical/default policy.

The owner now requests a real graphical VM/image to validate while development
continues. Follow [today delivery execution](PHASE-2-TODAY-DELIVERY.md). Complete
plan delivery remains the target; basic-tested intermediate media is not G2.
Actual base unpack passed321configured packages. Historical pre-intent resource
qualification and its correction89d2888 remain recorded, but the current live
root is at the failed account-recovery intent described above. No ISO exists yet.

## Basic-tested MVP delivery current

Owner explicitly reduced the delivery gate to basic MVP checks on 2026-11-16;
see [ADR-0249](adr/0249-owner-prioritizes-basic-tested-mvp.md). Prioritize actual
graphical task/Stop and bootable/installable media. Defer expanded qualification,
matrices and polish, publish known limitations, and retain honest B-story/G2
status. No extra harness development may delay the working delivery.

Actual MVP preparation: installer6/version0.2.0-1+toddy4 installed and native
postchecked0/0. Its34declared source files match the host/builder coherence map
4c23380a69cb4bdad73e4246385ce6ddb6043d417aca8a5e60fb3bc0f50571c5.
Base/live native requirements passed321/329packages and19cache bindings each.
MVPprojection3 passed; fresh export5 is current. Earlier projections/exports and
installer4/5 receipts remain retained, never overwritten or relabeled.

Historical expanded-cache custody: H10 full host archive verified; deletion's
postcheck limit failed after effect. A NEW independent postcondition companion
passed with3,782,561,792B actual guest gain; the old intent remains unchanged.
H11 custody completed normally with3,601,137,664B gain. All original media and
accepted backings remain retained. Two inactive historical builder backups were
fully gzip/roundtrip verified and retired, gaining7,493,423,104B host space.
A second fixed inactive pair is prepared for further admission, not yet executed.

Five actual source TARs (4.13GB) and a57MB inventory cover329export2 packages.
The exact per-package coordinator material/license review is recorded in
[evidence](evidence/mvp-source-coordinator-review-1.json), with independent
[current-functional admission](current-functional-source-admission.md).
Historical fingerprints remain incomplete and binary reproduction/G2 are not
claimed. Final export5/newinstaller4 still needs actual changed-package accounting;
no export2 source decision silently authorizes it.

Core4 actual GDM login, native package bytes, broker capabilities and shortcut
registration passed. Activation/focus failed an AT-SPI deadline; read-only journal
triage found no Python crash. No assistant GUI/task acceptance is inferred. Use
the fixed direct live-owner launcher and manual capture on the first actual MVP
ISO; do not repeat blind candidate boots. No MVP ISO/G2/physical acceptance yet.
The private runtime pointer names actual jobs; only the coordinator writes a guest.

## B06 native assistant integration current

Owner resumed2026-11-16 with maximum simultaneous isolated source subagents
([ADR-0229](adr/0229-owner-resumes-parallel-phase2.md)). B01-B05 accepted:41%
weighted Phase2. Native broker4 passed exact request recovery, authenticated root
routing, ordinary managed shell detached-descendant Stop, service-main-loss
cleanup/restart uncertain/no replay. Root control2 and owner7 remain reusable.
[Combined receipt](evidence/B04-native-broker.json); failed broker1/2/3 retained.
Current final context `.local/phase2/native-executor-broker-4`: QEMU/container0,
no guest writer, both accepted B02 backing files unchanged. Never replay it.

Native recovery2 passed broken consumer rollback/service restart, private manual
rescue backup, crash after effect before outer completion, owned readback after
restart with unchanged mtime/no replay, and manual drift without automatic undo.
[Receipt](evidence/B05-native-recovery.json). QEMU/container0 and accepted B02
backing files unchanged; no guest writer. Failure recovery1 retained. Never replay2.

Native profiles1 also passed canonical user-service/CLI task pin/rollback,
sealed FD lifecycle, old-profile exact lookup and restart/no replay. Source
memory/automation and native UI controls integrated with focused regressions.
B05 completed: native recovery3 passed actual atomic boot-config Stop before/after
commit with exact original bytes restored. [Receipt](evidence/B05-native-recovery-final.json).
No partition/firmware/installer claim. B06 is current.

Host custody COMPLETE: `.local/phase2/cold-installer-chunk-custody-1`,1840chunks,
originalSHA536109a5...57785fd reconstructed/verified, exit0,34.3GiB reclaimed.
[Receipt](evidence/B12-installer-capacity-custody.json). All primary/current
recovery/backing identities unchanged. Never replay; placeholder is NOT bootable.

Immediate native queue (one guest/package writer):
1. Native recovery3 completed0; never replay it.
2. Candidate overlays prepared/started successfully (ADR0239); never replay prepare/start.
3. QtBase attempt2 compilation/stage/consumer passed. Upgrade3 installed actual
   qtbase6.11.2-1+toddy2; shared dispatcher receipt timing bug was fixed and a
   separate read-only reconcile4 passed all4469installed payload paths/native
   consumers (0/0). Do NOT reinstall Qt. Failed2/3 receipts remain retained.
4. Actual Calamares3.4.3 native package and original branding/assistant/agent/
   executor/installer-branding/voice/integrations packages installed and checked0/0.
   [Native package proof](evidence/B06-native-source-packages.json). Desktop UI,
   voice engines/model/catalog, actual installer disks and B06+ acceptance remain.
5. Custom installer attempt3 compiled/qualified/installed/postchecked0/0 against
   current offline-capacity Python payload; original Qt/Calamares reused.
   dosfstools4.2 built39PASS/one upstreamXFAIL, qualified and installed0/0.
   [Native FAT proof](evidence/B12-dosfstools-native.json). Installer2 failed
   prewrite dependency check/changed0 and remains retained. Never replay it.
   Native background-defaults2 upgrade and installed user-override/reset check0/0;
   graphical B11 review still pending. Image projection1 now measures actual
   current native archives before offline/live composition/signing.
6. H10/H11 opaque tar custody completed: full decompression/hash verification,
   actual7,462,944,768B guest space recovered, all other evidence/ISOs/backings
   retained. [Receipt](evidence/B12-opaque-cache-custody.json). Never replay.
7. Current boot9ac84ac8-fe0e-41c0-a128-a8e4ad4bebf2, one root guest writer;
   scratch UUID58e1a631-07a2-40a1-87c2-49de37a69345. Private runtime pointer
   `.local/phase2/runtime.json` and actual guest markers govern continuation.
   Next: inspect projection1 and actual storage bounds; finish coherent voice
   native2 cohort, then combined actual native assistant desktop qualification.
   eSpeak1 RUNPATH and Whisper1 nonexistent-license failures remain retained.
   Corrected coherent native2 engines/model installed/audited/checked0; real
   attributed EN/PT inference WER0, about3s/sample. [Proof](evidence/B09-native-engine-files.json).
   Process2 four tests0 but original transport failed without pw-cat. Failed
   PipeWire2 upgrade remains retained; exact frozen PipeWire1 restore0/0 and
   separate pipewire-audio-tools attempt2 install/check0/0 preserve reverse pins.
   New process native2-r1 passed actual Stop/transport; reconciled catalog native
   installation and independent check0. [Proof](evidence/B09-native-process-reconciled.json).
   No GUI/PTT/device/physical acceptance. Assistant core1 collection failed before
   generation creation at strict legacy source-cache ownership; protected explicit
   frozen-model custody is next, then collect/cold-stop/bind/real graphical boot.
   Projection1 offline/live root bounds6,129,459,200/6,264,504,320B measured.
   Candidate-only180→204GiB growth completed0, independentguard0, full-root
   changed_paths0/acceptedbackings unchanged; targetfree48,323,973,120B.
   [Receipt](evidence/B12-candidate-target-growth.json). NEVER replay growth.
   Agent revision2 actual native archive built0 without installation; primary
   agent1 remains installed. Revision2 metadata signed on the private host; native
   GPGv verified both signatures and rejected tampering.
   [Proof](evidence/B13-revision2-native-crypto.json). Public lifecycle remains pending.
   Keep16GiB target/100GiB host reserves and measure actual per-stage demand.

Owner requested process/parallelism improvements2026-11-16. Keep three source
workers continuously assigned to independent commits. New Qt/voice build recipes
use up to8compiler jobs, bounded by actual CPU/RAM with2GiB reserve and recorded
/build/build-budget.json. Existing global build/package lock stays exclusive;
no second guest mutator or unqualified parallel-build infrastructure is enabled.
Reviewed native source-package wrappers now preserve complete B01 vendor/legal
custody, dependency/target-space preflight and actual installed-byte ownership
postchecks; [operator guide](native-source-package-delivery.md). Their source checks
passed770tests; archive/install/runtime gates remain pending. Metadata sync reused
2114inputs and updated248; it omits unchanged foundation reference retransfers.
Stage preparation/source review can overlap healthy native jobs; no unchanged
long foundation suites or pointless repeated downloads. Measure actual time/peak
usage before changing budgets again. Host100GiB+512MiB/target16GiB reserves remain.
No Phase2 ISO/G2/physical acceptance.

## Last verified runtime and jobs

Actual final context is
.local/phase2/native-desktop-final-runtime-1, phase native-desktop-final-verified,
controller/QEMU0, original current target backing unchanged. Normal GDM/PAM owner,
actual Tecla50 US lower/upper/focus/close and Git2.55 ordinary navy Terminal/repo
verified. Fixed800x400 viewer did not tile; no640px claim. First greeter capture
bounds boot-to-login <=28.6s. All native containers stopped, builder stopped/removed;
no guest writer or live OS job remains. Latest builder boot was
0110a6f4-8bfe-4b31-9375-1a3026021711. Never use an old PID as a resume command.

Current native Git source/compile/full test/stage0, original job1 collector failed
only because upstream removes individual counts. Qualification2/native install/post0/0
passed without replay. 1046shellgroups/31993success/0failed/388knownbroken/454skip.
351owned Git paths, native target root0:0. Actual UID101/NNP local repo/merge/clone/
fsck/dirty checkout preservation/credential refusal plus actual UID12402 Terminal.
Git archive47fd49e06be6c538ee9d0749365a89e7e7cccb95c455f356c105f141717a708e.
Original prepared source recipe3535b2c4 immutable; do not reprepare/rebuild/retest/
reinstall it from old logs. Receipt build/b02-git-install.success.json.

## Verified acceptance to reuse

Normal GDM owner/browser153.7.0esr/Files+Trash/Editor/Settings/Terminal/virtual HDA
sound+mute/NM GUI+DHCP+DNS+HTTPS+policy and fallback/restoration passed. Actual
installed kernel2/FUSE helper owner/otherUID/allow_other/unmount/SIGTERM and original
signals0; portals dark/light/dark and chooser allow/cancel/Close passed. Offline
Editor protected save/auth cancellation/actual autosaved29B crash recovery/SaveAs,
subsequent distinct boot file/user teal+dark/NM state and owned foundation recovery
entry passed. Real screenshots retained; no HTML mockup/physical/provider blanket.
15second desktop idle max408.273MiB (MemTotal-MemAvailable), four-CPU nonidle0.0333%.
360native inventory/308package projection with legal/source hashes,52unselected
integration packages for B12 composition review; no blind removal/composed ISO claim.
Optional catalog candidates remain unavailable; Git is native base, no mise.

## Cache custody and exact resumption

Git /sources/phase2/work/git-1 was1536MiB RAM and vanished on cold stop. Qualified
archive persists in builder /var/cache/toddy/build/git-2.55.0-qualified-1.tar.gz,
237578723B SHAe1cca99c2c21213f9a5d90834abe1ba6085b794dba4f41b61ef156c7b723b7c2.
Guest /var/log/toddy/phase2/git-cache-custody-1.json complete: actual6824entry restore
bytes/modes/owners/mtime/symlinks/hardlink classes exact. Original extraction root
mode umask mismatch repaired only by restore owner101, no extraction replay;
archive includes original workspace root1777. Restore with same-permissions into
new isolated owned RAM work only if needed, verify complete inventory/receipt,
then restrict the workspace mount root0755. Do not run prepare_git_input.py again.
Do not stop source/data custody checks merely because a success marker exists.

On owner resumption: inspect actual Git/main/status/cold disk identities in stop
receipt, B04 retained blocker and actual prerequisites; read B04/needed contracts.
Start the same designated builder only if needed, guard /mnt/lfs and serial
TODDY-LFS-TARGET/new boot/actual jobs before mutation. Restore only caches required
by that slice using NEW receipt names. Do not replay trim/provisioning/retirement/
installs or old runtime controllers. Keep one guest writer and persistent failure
ledger .local/phase2/failures.json; budgets do not reset across compaction.

## Final repository/public handoff

After each validated slice: make check/dashboard, secret scan, commit/push and
verify the public dashboard against that exact HEAD. Continue eligible Phase2
work; the historical B02 stop is superseded by ADR-0229.

## Recovery and unchanged evidence

Previous native browser/default-GDM/security/TLS/offline/Stop/restart, Files/Trash,
Editor ordinary save/relaunch, NetworkManager GUI/DHCP/DNS/HTTPS/polkit/manager
recovery, navy/Terminal/virtual HDA sound/mute proofs are retained. Reuse unchanged
component evidence; new kernel/FUSE/portal scope still needs affected real boot.

Historical desktop1 cache restore receipts COMPLETE in the earlier boot (mounts
are gone after cold stop; only Git work was newly prepared in0110a6f4): six persistent volumes/Glycin/kernel,
generation4RAMcache85958entries, original browser6aliases/archive/security4aliases.
After a future cold boot use NEW receipt names; never replay desktop1-* or network2-*.
Kernel raw scratch2GiB exact serialTODDY-B02-KERNEL,
UUIDc6c4176d-faed-4ee3-9ae0-94914a0af666; host kernel-fuse-growth.json full allocation/
parent chain and guest kernel-fuse-resize-1.json COMPLETE. Never resize/reformat again.
W=/mnt/lfs/sources/phase2/work/kernel-landlock-1; preserved COW/source/baseline and
qualified candidate kernel archive, old redundant stage retired only after actual
full archive restore proof. New candidate native stage currently retained there.

Browser raw16GiB serialTODDY-B02-FIREFOX/UUID082a2d97-fa79-4ee5-86e5-a179f768daec,
BASE=/mnt/lfs/sources/phase2/work/firefox-1. Original153.2 source/objects retired
markers; archives/retained ELF proofs intact. After cold recovery restore existing
volumes then restore_browser_work.py NEW, firefox_archive_storage.py --restore NEW,
restore_firefox_security_source.py NEW; no extraction/compiler replay.
Generation4 scratch archive .local/phase2/settings-scratch-custody-4/scratch.tar.gz,
SHA194480fde5b0e4fefd3cb947b9894150820824428a8e3245aae7ee12a5150ba9;
phase2_restore_settings_scratch.py --generation4 --receipt NEW. Source/work for
Fuse and portal base are persistent target files; restore readonly self-bind only
when cold postconditions show it absent, never reprepare existing directories.
Host100GiB/target16GiB/scratch128MiB reserves and failure ledger persist.

