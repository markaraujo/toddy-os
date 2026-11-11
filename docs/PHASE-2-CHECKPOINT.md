# Phase 2 continuation card

Owner boundary: **complete ALL B02, then stop before another story**. Full Phase2
Goal active/incomplete; B01/B03 accepted13%, B02 in_progress, B04-B13/G2 pending.
Physical foundation tests unperformed. No Phase2 ISO. Preserve G1 master/evidence.

## Current slice: native default-boot/browser interaction validation

Builder RUNNING boot e146fad4-b1e4-4199-9935-3223e693a00b. No live writer remains:
compiler2/controller94430, stage1/controller49676, archive storage1/controller54653,
package install1/controller46573, readonly verification3/controller64497 and
boot policy1/controller48206 are terminal. Never replay these operations.
Git/actual receipts/processes/mounts, not this card, are authoritative on resume.

**Browser installed:** Firefox153.7.0esr-1+toddy1/amd64,815owned payload entries,
archiveSHAba566c57d612640cc0342f374f64f7853bacdab6d0af6c1e38b37bdd085233b0.
[Installed verification](evidence/B02-firefox-install.json): readonly recipe/post0/0,
zero installed-root changes; actual UID101/NNP version153.7.0esr and native desktop
entry passed. Actual17ELFs/37native library providers pinned, all source notices
retained. Original install backend completed but own comparison included two
DEBIAN control entries: original recipe1/post-not-run/801rootchanges preserved.
Verify2 archive/stage recipe0 reused; its post1 lacked chroot procfs. Verify3 uses
private procfs, global mounts unchanged. **Do not reinstall** because original
firefox-package-install-1.json still says installing; current package/verify3
success are authoritative. Builder userns EPERM warning remains in CLI evidence;
actual LFS content sandbox and GUI are NOT yet accepted.

**Compiler/stage passed:** [Compile](evidence/B02-firefox-security-compile.json)
2508.366s/0,153.7.0/ELF64x86_64/no reserve stop; independent hashes retained.
[Stage/storage](evidence/B02-firefox-security-stage.json)4.561s/0,65entries,
294038937bytes, desktop/nativeGLib/exact5icons/relative launcher, conservative
stage inspection. Original compiled ELF artifacts unchanged by upstream stripping;
staged runtime hashes separate. Never repeat configure/compiler/mach install.

**Graphical startup configured:** [Policy](evidence/B02-desktop-graphical-boot-policy.json)
recipe/post0/0,2generated native Systemd links changed, offline wait mask preserved.
Default graphical.target and display-manager.service->owned gdm.service enabled.
No unit/PAM/security/user-profile change; original exact foundation default checked.
CLI emitted missing chroot proc/sys warnings but actual links/postconditions passed;
actual power-on GNOME is still unproven. Do not replay successful migration.

## Exact next action

Native browser controller/probe and URL/text QMP input are implemented locally.
Next: finish focused repository checks, commit reviewed inputs, then dispatch ONCE
`python3 scripts/host/phase2_native_browser.py` with log
`.local/phase2/native-browser-controller-1.log`. Context
`.local/phase2/native-browser-runtime-1` must be absent before first dispatch.
No native browser job has been dispatched yet. Readonly preflight log is
`.local/phase2/browser-preflight-1.log`; verify its terminal exit before use.
Test selection: input encoding two cases, Python syntax, repository make check;
actual new graphical boot/browser scope next, unchanged foundation suites reused.

Preflight actual installed browser/GDM/GTK/kernel inputs and current cache/mount
state, retain accepted exact descriptors. Stop builder once only after preflight,
then fresh disposable overlay with readonly base, guard serialTODDY-BOOT-TEST,
actual kernel7.1.8-toddy/PID1 and unchanged backing check. One guest writer.
Use desktop-boot-probe.service (Type=exec/RuntimeMaxSec900), not old oneshot wanted
by multi-user: target implicit After would otherwise delay normal graphical boot.
Never manually start GDM for this default-boot acceptance. Wait actual graphical
and GDM active, normal owner login via private control/QMP (no autologin/PAM bypass).
Keep existing foundation probes and source master unchanged.

Serve tests/fixtures/browser-smoke on guest loopback as disposable normal owner;
these HTML files are test data, never GUI acceptance. Actual GNOME launcher open,
Firefox view/navigation/input/focus/readable narrow/maximized windows, close/reopen
with independently observed PID/start identity and same profile/stored value.
Capture native scanouts. Verify actual Web Content UID/NoNewPrivs/seccomp and
public TLS/offline-failure/Stop behavior at affected scope; never disable sandbox
or treat builder CLI warning as native sandbox evidence. Do not dump credentials,
process environments or browser personal data. Test account has no real secrets.
Retain failed scopes, reuse unchanged network/Files proofs, no broad matrices.

After terminal native job reconcile container/image/report and restore existing
builder/caches with NEW receipts; never restart/replay based on PID or timeout.

## Existing caches/recovery (never prepare/format/recompile again)

Base browser volume16GiB serialTODDY-B02-FIREFOX/UUID082a2d97-fa79-4ee5-86e5-a179f768daec.
BASE=/mnt/lfs/sources/phase2/work/firefox-1. restore_browser_work.py NEW-name after
base volumes restores original6aliases/retained ELFs. Old153.2source and obj are
retired markers, not usable inputs. [Source recovery](evidence/B02-firefox-baseline-source-custody.json)
actually restored/verified468620files before retiring children;509834inodes freed.
Original archive807705672B/SHA c443c99704aadaf60fb267d709c42bc283e49e82292084f976369c8327ad833c
now at BASE/security-source-archives with readonly original /mnt/lfs/sources alias.
After cold base restore ALSO firefox_archive_storage.py --restore NEW-name;
underlying empty placeholder is not an archive. Private restore/replay refusal0.

New source/work and4aliases: restore_firefox_security_source.py NEW-name after
base restore. Source153.7 archiveSHA7f8715ee7de2cf36a156216a9b1c7f26d1653010e65793bb2fce66e12edb6ea0;
source immutable, work alias firefox-security-1537-1. Source complete verified
469024files/3515456965bytes. Raw work/stage data persists. Finished promotion alias
/sources/stage/phase2-firefox-security-1 is not needed for installed runtime;
rebind only if explicitly needed with actual source/record inspection.

Other existing6volumes via virtual_discard_checkpoint.restore_volumes() FUNCTION
ONLY (never trim/main), Systemd source prepare_systemd_pam_input.py --restore,
Glycin/kernel COW helpers with NEW receipts. Generation4 archive
.local/phase2/settings-scratch-custody-4/scratch.tar.gz485113684B/SHA
194480fde5b0e4fefd3cb947b9894150820824428a8e3245aae7ee12a5150ba9,
restore with phase2_restore_settings_scratch.py --generation4 --receipt NEW-name.
Existing network2 recovery receipts COMPLETE, never reuse names. Preserve100GiB
host/16GiBtarget/128MiB scratch and inode reserves. Full failure ledger remains
.local/phase2/failures.json; attempt budgets survive compaction.

## Still due before B02 stop

Native browser/default boot/security/TLS/offline/restart; restoredNM reboot
persistence; audio playback/controls; navy/default style and Terminal rendering;
Editor refusal/recovery/reboot; affected device/refusal checks; absent-agent use,
minimal manifest/optional-catalog status, boot/idle measurements and recovery boot.
B02 is NOT complete. No further B story before requested stop after all B02.
