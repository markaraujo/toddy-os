# Phase 2 continuation card

Owner boundary: **complete ALL B02, then stop before another story**. Full Phase2
Goal active/incomplete; B01/B03 accepted13%, B02 in_progress, B04-B13/G2 pending.
Physical foundation tests unperformed. No Phase2 ISO. Preserve G1 master/evidence.

## Current slice: missing FUSE/desktop portal integration

Native desktop integration runtime1 TERMINAL, QEMU0/report true/WAV capture
verified, source backing unchanged. Normal GDM owner/navy/Terminal UTF8+echo/tiled
view/automatic PipeWire+Pulse+WirePlumber/HDA/paplay/mute pass. Evidence
[evidence/B02-desktop-native-integration.json](evidence/B02-desktop-native-integration.json).
No physical audio claim. Settings light despite prefer-dark; actual dpkg confirms
xdg-desktop-portal and GNOME backend absent. Missing selected dependency is next.
Builder RUNNING boot0c29ac3a-aa02-49fb-af6c-0df420c43012. All desktop1 cache
restores COMPLETE0: six volumes/Glycin/kernel, generation4RAMcache, original browser
6aliases/archive and security4aliases. Last host restore session4747 exit0;
`.local/phase2/desktop1-browser-cache-restore.log`. No guest writer remains.
Never replay any desktop1-* receipt or reinstall accepted packages.

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
actual native browser GUI/content sandbox were later accepted at B02-browser-native.json.

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
actual power-on GNOME later passed in B02-browser-native.json. Do not replay successful migration.

## Exact next action

FUSE kernel corrected build2 COMPLETE0/15.003s, minimum1091739648Bfree,
config ONLY FUSE_FS n->m,20old module hashes/93715source entries unchanged. Original
build1 reserve-stop retained. Online same-file1->2GiB growth COMPLETE/allocation
reconciled/parent chain/guest UUID/config retained. Do not replay growth/build.
Kernel candidate SHA0482366cc51727f76af11611275b7124bcd9aadbd76d231ca6fd44d22cb0dc77,
fuse.ko SHAce3b8f53643839d98fec304561376bf3c6ae873c519468a57b15f3e723111ae2.
Fuse3.18.2 source prepared/85targets built. First own test selection wrongly
included real-mount signal driver; preserve failed log. Stage2 COMPLETE0 reuses
compiler outputs,2non-mount upstream drivers and helper version/refusal pass.
Native mount/signals/root helper/denial/recovery tests remain pending, not skipped.
No native FUSE/kernel package installed. Host/guest source caches persist.
First native-kernel-fuse-1 BIOS diagnostic is TERMINAL failure: actual kernel/
FUSE module load passed; UID101 open failed because static diagnostic lacks udev.
Actual installed Systemd261.2-1+toddy3 50-udev-default.rules owns FUSE MODE0666;
bytes independently match package record. No installed permission/security change.
Correction1 new C diagnostic applies only that rule in its own volatile devtmpfs,
adds child status on failure. New boot-prepare2/controller10707 COMPLETE0, canonical
C SHAc56c1dfc3e4ae53c86f82011e46745552d05db562c9071ff5ba4b83ee147f630,
initramfs SHA c93df43f9f3504b2310555b12917a04ae44ad99db02c6461f3c0536f9689d176.
Kernel/source/module bytes unchanged; no compiler/kernel replay.
Next commit reviewed correction then run ONCE
`python3 scripts/host/phase2_kernel_fuse_boot_retry.py` using fresh
.local/phase2/native-kernel-fuse-2 (must be absent before first dispatch).
Native FUSE device/UID/denial/unload and Landlock/seccomp/namespaces BIOS+UEFI gate,
then native package/mount/signals/helper policy and actual portal/appearance.
Original failed context1/report/log retained; budget in failure ledger survives.

Test selection: changed input/syntax plus make check381, readonly native report
reconciliation and real QMP scanouts. No foundation suite repeated.

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

RestoredNM reboot
persistence; portal dark/light integration;
Editor refusal/recovery/reboot; affected device/refusal checks; absent-agent use,
minimal manifest/optional-catalog status, boot/idle measurements and recovery boot.
B02 is NOT complete. No further B story before requested stop after all B02.
