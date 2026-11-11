# Phase 2 continuation card

Owner boundary: **complete ALL B02, then stop before another story**. Full Phase2
Goal active/incomplete. B01/B03 accepted13%; B02 in_progress; B04 integration
blocked, B05-B13/G2 pending. Physical foundation tests unperformed. No Phase2 ISO.

## Current slice: native network remaining recovery

Original native network controller TERMINAL1 (aggregate test failed), context
.local/phase2/native-network-runtime-1, input commit df30c6f. Container actually
exited0/no OOM; backing unchanged. Builder stopped/removed. Never replay original
GUI actions or package install. [Native prefix](evidence/B02-network-native-prefix.json)
retains normal GDM/PAM/Wayland owner, real Settings connected/OFF/ON transitions,
DHCP/routes/DNS/HTTPS200 and two active-client polkit passes, plus seven real PNGs.
Original failure: recovery networkd actually acquired DHCP, but the probe expected
an unavailable private lease file. Aggregate remains failed, B02 incomplete.

### Exact next action

Commit reviewed remaining-only controller/probe and prefix evidence, then run once:
`python3 scripts/host/phase2_native_network.py --remaining-recovery`
with log .local/phase2/native-network-recovery-controller-1.log. New context
.local/phase2/native-network-recovery-runtime-1 must not already exist. Controller
verifies prior report, stopped container and unchanged base, layers a new writable
overlay over the retained first overlay read-only, leaving both inputs unchanged.
No login, package install or GUI state writes replayed. Probe verifies retained
networkd selection before writes, public `networkctl --json=short dhcp-lease`
(Systemd261.2 source), address/routes/DNS, then continues stop-networkd,
restore-marker/start-NM/DHCP/DNS. Actual outcome pending; timeouts are failures.
One writer, ordinary bridge/user NAT, original target guard and unchanged schemas.
Focused preparation check: make check377passed. Failure ledger retains one prepared
correction/no failed corrections; do not reset its budget on resumption.

On terminal inspect report/container and both backing identities. Only then restore
builder once and existing6volumes/Systemd/Glycin/kernel/generation4/browser mounts
with NEW receipts. Browser helper qualified private namespace only; actual cold
restore still pending. [Proof](evidence/B02-browser-mount-recovery.json).
No format/resize/source/compiler replay. Original network package install0/0
remains complete; [installation](evidence/B02-desktop-network-install.json).
NetworkManager D-Bus VERSION1.58.1; CLI ToddyOS banner intentional.

## Browser compiler, security and persistent build volume

[Original compiler](evidence/B02-firefox-baseline-compile.json) TERMINAL0/compiled,
2485.345s; independent ELF SHA/x86_64 and exact AppVersion153.2.0 verified.
No reserve cancellation, final7,260,672,000B available. Private feasibility ONLY;
ADR0225 blocks its browser delivery due later high-impact upstream corrections.
No old browser package/install/runtime acceptance. Original work/logs retained.
Guest controller receipt /var/log/toddy/phase2/firefox-build-controller-1.json;
wrapper /var/log/toddy/phase2/firefox-build-1.log/.exit; work
/mnt/lfs/sources/phase2/work/firefox-build-1 with compile result/log. Never replay.

Corrected153.7.0esr800,080,060B archive cached.local/sources, publisherSHA512
matched, SHA2567f8715ee7de2cf36a156216a9b1c7f26d1653010e65793bb2fce66e12edb6ea0.
Separate firefox-security-1537 lock, original source retained; no signature claim.
[Security review](evidence/B02-firefox-security-review.json) and
[source metadata](evidence/B02-firefox-security-source.json): host scan complete,
510,287members/3,515,456,965regular bytes/21critical files. Root/toolkit configure
unchanged; Rust configure vendor-target changes. Header versions alone do not
clear NSS/NSPR security/ABI or actual minimum Rust constant. Overlay source/work/
configure/compiler/stage/install/native security/UI all pending. Old objects are
not a qualified cache for changed source. Measure capacity and choose qualified
custody/retirement before fresh overlay work; do not lower reserves.

Browser raw file.local/vm/phase2/firefox-scratch.raw,16GiB/full allocation,
receipt firefox-scratch.json; inode11956378/device66306. SerialTODDY-B02-FIREFOX,
UUID082a2d97-fa79-4ee5-86e5-a179f768daec. Existing filesystem mountednosuid,nodev
at /mnt/lfs/sources/phase2/work/firefox-1 (BASE below), actual/dev/vdd currently;
never assume device name or format/reprepare. Current persistent aliases:

- BASE/source/firefox-153.2.0 self-bindRO and inputs/firefox-153.2.0 RO.
- BASE/tools/wasi-sdk-25.0-x86_64-linux self-bindRO.
- BASE/build/browser-1 -> work/firefox-build-1 RW (compiler/cache/logs/stage).
- BASE/source/nasm-3.02 -> inputs/nasm-3.02 RO.
- BASE/build/nasm-1 -> work/nasm-1 RW (private qualified NASM stage).

Alias roots inputs/work mean /mnt/lfs/sources/phase2/inputs and work.
Receipts /var/log/toddy/phase2/firefox-work-volume-1.json, firefox-source-1.json,
browser-tools-input-1.json and nasm-input-1.json. These are existing mounts/data;
restore only with new unique receipts after checking actual mount state.

[Private SDK/tools](evidence/B02-browser-wasm-tools.json) qualified UID101/caps0/
NNP/no-egress/no-secret paths/source-system-tool mutation denial and C/C++ WASM
compile/link; NASM3.02 exact assembly/link/exit42/disassembly passed. No OS tool
install. [Configuration](evidence/B02-firefox-configuration.json) passed after
one bundled PNG1.6.58/APNG choice preserving system PNG, all6WASM/main sandbox
flags and Wayland enabled. Original failures retained/resolved; no replay.

## Closed host storage operations — no live producer / never replay

[Native capacity custody](evidence/B02-native-capacity-custody.json) COMPLETE0:
178verified chunks/5,949,423,616bytes, whole original SHA
7f4af9ce2e3002dff261b64035f1ab9b6f4ce1d28112fae00a270704fd686dab.
Controller1595927/start29884400 TERMINAL/process absent; unchanged producerSHA
bd0108e9268d0d139276b319fa27c5133e9e3c5fc1e09142412b1c4a8f6ed428.
Private context.local/phase2/cold-native-chunk-custody-1/result.json, log
same context stem-controller.log. Host113,188,540,416B free at terminal success.
Original old GCC builder path absent; source.custody hole skeleton NOT BOOTABLE.
Archives retain exact bytes; reconstruct ordered chunks with sufficient capacity,
whole SHA/length and QEMU check before use. Native/cold locks released.
Existing math/firefox-target custodies COMPLETE/untouched. Never replay them.
Active/backing/foundation-master images unchanged.100GiB host/16GiB target/128MiB
scratch reserves remain required at every operation.

## Retained native proofs, packages and other cache recovery

[Files gate](evidence/B02-files-native-combined.json): actual GDM/PAM owner/Wayland,
local operations/Trash restore/watched content, gio Trash0, activeFilesPID polkit
challenge2/no credentials passed. Old failures retained; no admin-write/share/
reboot/hardware claim. [Terminal defaults](evidence/B02-terminal-defaults-install.json)
installed/CLI-qualified7actual cases; native prompt rendering pending. Existing
owner Editor open/type/save/relaunch/maximize/Terminal checksum and Settings
navigation proof retained, global theme/network/audio integration still pending.
GDM50.2/Shell+Mutter50.4, Nautilus50.2.2, Gvfs1.60.2, LocalSearch3.11.1,
GTK4.22.4-1+toddy13. Keep approved foundation/kernel7.1.8-toddy/source versions.

Generation4 archive.local/phase2/settings-scratch-custody-4/scratch.tar.gz,
485,113,684B/SHA194480fde5b0e4fefd3cb947b9894150820824428a8e3245aae7ee12a5150ba9.
Qualified restore85,958entries/42,228regular inode classes/20aliases; current
firefox1-scratch-restored-1 COMPLETE. After future cold restart restore SAME6volume
UUIDs/inodes via virtual_discard_checkpoint.restore_volumes() FUNCTION ONLY,
never trim/main; same Systemd source (--restore), Glycin companion and kernel COW
with NEW receipts. Kernel scratch remains1GiB/UUIDc6c4176d-faed-4ee3-9ae0-94914a0af666;
never format/resize/rebuild. Then phase2_restore_settings_scratch.py --generation4
--receipt <NEW-name>. Also restore browser volume/aliases above using restore_browser_work.py
<NEW-receipt> (existing mounts only) before another compiler/native transition. Reconcile actual mounts/receipts
on interruption, never replay completed recovery.

## Still due before B02 stop

Corrected browser/security/ABI/native UI; native networking/polkit; audio playback/
controls; affected devices/refusal/recovery; navy/global theme and Terminal GUI;
Editor refusal/recovery/reboot persistence; offline/absent-agent use; minimal
manifest/optional catalog status, boot/idle resources and recovery-entry boot.
Preserve scoped successes, widen only for changed inputs/essential final gates.
Complete ALL B02, then STOP before another story. No physical support claim.
