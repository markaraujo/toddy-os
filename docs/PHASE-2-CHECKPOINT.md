# Phase 2 continuation card

Owner boundary: **complete ALL B02, then stop before another story**. Full Phase2
Goal active/incomplete; B01/B03 accepted13%, B02 in_progress, B04 integration
blocked, B05-B13/G2 pending. Physical foundation tests unperformed. No Phase2 ISO.

## Current slice: compiler feasibility and browser security overlay

### Security acceptance boundary — ADR0225

Current upstream review found high-impact same-ESR corrections after153.2,
including MFSA2026-127 released2026-11-10. Baseline153.2 is NOT browser-release
eligible. Finish the healthy current compiler once as private feasibility only;
never install/promote its output as the delivered browser or use owner credentials.
No mutation/restart/second guest writer. [Review](evidence/B02-firefox-security-review.json).

Separate firefox-security-1537 source appended to phase2 lock, original retained.
Official153.7.0esr archive800,080,060B matches publisherSHA512; SHA256
7f8715ee7de2cf36a156216a9b1c7f26d1653010e65793bb2fce66e12edb6ea0,
already cached.local/sources/firefox-153.7.0esr.source.tar.xz. No signature claim.
Host source scan session35200 TERMINAL0:510,287members/3,515,456,965regular
expanded bytes;21critical metadata files retained/hashed. [Source review](evidence/B02-firefox-security-source.json).
Root moz.configure/toolkit/moz.configure unchanged; Rust configure changes vendor
alias selection. Candidate headers NSS3.125.1/NSPR4.39; installed3.126/4.40.
These observations are NOT compatibility/security acceptance. Exact minimum Rust
constant and NSS security/ABI coverage still need fresh source review/configure.
Private complete scan.local/phase2/firefox-security-source-review-1/result.json,
selected source texts retained there. Never rerun completed unchanged scan/fetch.
Host free108,326,338,560B versus107,374,182,400B reserve, only952MB headroom:
no new large host allocations. Guest raw compiler scratch remains preallocated.
No guest mutations/new extraction/install while original compiler holds writer.
Next host action: prepare affected overlay storage/recipe and notice plan without
changing active producer/inputs or allocating unchecked space.
Next guest action only after baseline compiler TERMINAL: measure capacity and
choose qualified custody/retirement/fresh overlay source/work/build. Old objects
not a qualified cache for different source. No guest153.7 extraction/install yet.

[NASM proof](evidence/B02-nasm-build-tools.json): frozen3.02 source SHA
87336eba53b4acfe917424ab5d500d2b0054d9f5148d35c2273ccf2cfb712f0d.
Guest nasm-build-1.exit2 (original600 Makefile.in unreadable toUID101);
nasm-build-2.exit0 after one metadata-only0644 correction of exactly3files,
original contents/failed logs retained, fresh configure directory.
Actual assembly/link/executable42/exact machine bytes/ndisasm positive control
passed. Private stage /mnt/lfs/sources/phase2/work/nasm-1/stage, sourcealias
/mnt/lfs/sources/phase2/inputs/nasm-3.02. No native OS install. Ledger resolved
one correction; NEVER replay NASM compiler/extraction/correction.
Firefox compiler now owns the single guest writer as recorded below.

Actual source inspection: Firefox requires Clang>=19 for WASM; installed22.1.8
has X86/AMDGPU only, no WASM/wasm-ld/ld.lld. ADR0224 chooses private official
WASI SDK25 bootstrap to retain upstream WASM decoding isolation. Native compiler/
foundation unchanged. Asset114,450,290B already cached.local/sources/
wasi-sdk-25.0-x86_64-linux.tar.gz, SHA
52640dde13599bf127a95499e61d6d640256119456d1af8897ab6725bcf3d89c.
Official tag/source/LLVM/libc/config revisions and15exact license/notice URLs/hashes
in config/phase2/browser-build-tools.lock.json. Local notices retained under
.local/phase2/wasi-sdk-25-notices. SDK extraction/execution qualification now passed as recorded below.

SDK preparation2 TERMINAL0, receipt browser-tools-input-1.json stateprepared;
original prepare1 failed BEFORE ANY receipt/archive/tools/alias writes from missing
metadata allowlist entry. That transfer cause resolved after one correction;
no extraction replay. Actual SDK root tools/wasi-sdk-25.0-x86_64-linux readonly,
all original files/modes/links inventoried. Browser tools probe1 TERMINAL0,
[actual proof](evidence/B02-browser-wasm-tools.json): UID101/caps0/NNP, no external
route, no credential/system paths, source/system/tool mutation denied; C/C++ WASM
compile/link0/expectedv1magic, NASM3.02 version positive. Existing compiler root
unchanged. Exact Firefox-only profile added to isolated.sh; tools readonly.
Affected CUPS/Samba exact base/result pins updated after sole-delta byte proof;
actual Bash tests confirm branch inactive for each. Full make check374passed.
No unchanged native CUPS/Samba/compiler/GUI suite replay.

[Configuration proof](evidence/B02-firefox-configuration.json): configure1 FAILED1
from absent system PNG/APNG symbol png_get_acTL; original log/recipe/mozconfig
retained. One correction selects source-bundled PNG1.6.58, preserves nativePNG;
configure2 TERMINAL0. Generated Wayland/systemNSS+NSPR+ICU/main sandbox and all6
WASM decoding library flags verified. No official branding/updater/crashreporter.
No source patches, foundation upgrade, sandbox disabling or package installation.

### Actual running compiler / exact next action

Tool session10663, localcontroller.local/phase2/firefox-build-controller-1.py,
log same stem.log. Guest controller11310/startticks in
/var/log/toddy/phase2/firefox-build-controller-1.json; boot474caba2. Last actual
/proc start match LIVE, compiler receipt state=running, C++/Rust/wasm2c output
progress observed. Guest wrapper log/exit /var/log/toddy/phase2/firefox-build-1.log/
.exit; build output /mnt/lfs/sources/phase2/work/firefox-build-1/firefox-compile-1.log,
compiler receipt firefox-compile-result.json in same work directory.
Command /src/mach build -j6; initial11,054,034,944B,128MiB floor+64MiB stop margin.
Configstatus SHA473c3553e5db79572726d1f068cfb6c75ee050355222a864eb23f008d44ac493;
mozconfig SHA899baac32c274db3e66781f19f7ff6d9e29866d92527a1198acd19ae4c2a31de.
One guest writer held by isolated.sh; DO NOT sync metadata, mutate guest, reboot,
start another writer or replay a compiler from a chat PID. Healthy long build
excluded from diagnosis budget. Source/private SDK/tools read-only, no egress.

Deterministic observer tool session51171,
.local/phase2/observe-firefox-build-1.py/.local/phase2/firefox-build-observer-1.log;
latest actual observation.local/phase2/firefox-build-latest-observation-1.json.
Observer checks controller boot/PID/start, log bytes and real terminal exit every
30s, reports only1MiB growth/5min/terminal. No repeated model calls for unchanged
logs. If observer deadline/error inspect SAME controller/job, never restart build.
Next: inspect actual live/terminal state and compiler receipt; on0 require both
ELF artifacts and exact application version for private feasibility evidence,
then follow ADR0225 security overlay/capacity gate. Do not stage/install baseline
for release. Never treat timeout/log
absence as success. Browser itself not accepted until actual runtime/UI evidence.
Host-only source/security/inventory review eligible while compiler owns guest.
Preserve100GiB host/16GiB target/128MiB scratch and final B02 stopping boundary.

Builder RUNNING boot474caba2-3085-4d07-bba0-e2548b5728d4. Controlled restart
controller firefox-builder-attach-restart-1 TERMINAL0. Existing recovery
firefox-builder-existing-recovery-1 COMPLETE0 (same6volumes/Systemd/Glycin/kernel).
firefox1-scratch-restored-1 generation4 COMPLETE0:85,958entries/42,228regular inode
classes/20aliases. [Recovery evidence](evidence/B02-firefox-work-recovery.json).
No compiler/package/native GUI replay. Prior boot8688d2de stopped cleanly.

Dedicated16GiB file prepared/attached once, host receipt
.local/vm/phase2/firefox-scratch.json, inode11956378/device66306,
serialTODDY-B02-FIREFOX. Blank-signature/partition/holder/mount checks passed;
mkfs0 without force/discard, UUID082a2d97-fa79-4ee5-86e5-a179f768daec,
actual/dev/vdd (DO NOT assume name later), mountednosuid,nodev at
/mnt/lfs/sources/phase2/work/firefox-1; initial16,713,080,832B available.
Guest receipt /var/log/toddy/phase2/firefox-work-volume-1.json state=mounted.
Host full allocation guard passes;100GiB host/16GiB target/128MiB scratch reserves
unchanged. NEVER repeat preparation/format/recovery. Required make check370passed.

### Retained source preparation

Source extraction session92782 TERMINAL0; guest receipt firefox-source-1.json
stateprepared/read-only source.509,835members/3,514,842,428expanded bytes,
11,704,008,704B available. Original archive SHA verified before extraction.
No configure/compiler yet. No running guest writer. NEVER replay extraction.
Local log.local/phase2/firefox-source-prepare-1.log/exit retained.

Source configured toolkit choices support cairo-gtk3-wayland-only; installed GTK3
is Wayland-only. No startup-notification reference found in actual configure files;
do not add unnecessary X11 dependencies or rebuild foundation.
Need source/compiler/security/ABI review, native install/UI/sandbox acceptance.
No official branding, example Google API key or sandbox relaxation. Book estimate
8.9GB/15SBU is not actual runtime acceptance. Source lock153.2.0esr SHA
c443c99704aadaf60fb267d709c42bc283e49e82292084f976369c8327ad833c;
bookBLFS13.1-systemd xsoft/firefox.html SHA
 e3fcd198bbfa3b8ecae24abce029c2a04809bc300c9dc295de92a9446889d0a8.
Clang22.1.8/Rust1.97.1/cbindgen0.29.4/Node24.19/ICU78.3/NSS3.126/NSPR4.40
available. Optional system codecs/startup-notification absent; inspect conditions.

## Other retained verified slices

[Files native gate](evidence/B02-files-native-combined.json) passed actual normal
GDM/PAM owner/Wayland/session2, local Files actions/Trash restore/watched content,
installed gio trash URI0, activeFilesPID authorization challenge2/no credentials.
Original URI/runuser failures retained/resolved, no fullB02/network/admin write/
reboot/hardware claim. Native2controller/container0/base unchanged.

[Terminal defaults](evidence/B02-terminal-defaults-install.json) installed
0.2.0-1+toddy1, archiveSHA2cdbca318a0b1f623eeb3ce5da84d0b95cda5ec900e425caf14a6ad94247841f.
Original test-quoting failure retained; verify-only0/0 ZEROroot changes, samepayload,
seven realUID101/NNP startup/custom/opt-out/plain/readonly/login/noninteractive cases
plus idempotence/hook/flags preservation. Existing homes untouched. Actual GUI
rendering pending. Do not reinstall/replay unchanged tests.

## Completed cold backup custody — never replay

[Capacity evidence](evidence/B02-firefox-build-capacity.json): controller1450932
TERMINAL0/process absent, statecomplete,1023durable chunks/originalwhole SHA
6b8f1ad2736c8f7a4f02f361272c1e27ca151ff76b59bcee70fed8f7a7c3c8e1
for34,298,068,992bytes. Oldh07-gcc-tested-target.qcow2 path absent; retained
source.custody is hole skeleton, NOT BOOTABLE. Restore from verified chunk archives
in order only with sufficient space, then whole SHA/length/QEMUcheck. Active/
backing/foundation-master untouched. Native boot lock released. Existing math
custody also complete/untouched. Host110,809,731,072B after16GiB allocation.

## Current packages, cache and recovery

Current builder boot474caba2-3085-4d07-bba0-e2548b5728d4; target /mnt/lfs on designated
virtual TODDY-LFS-TARGET (/dev/vdb4), one writer build.lock. Native7.1.8-toddy.
GNOME Shell/Mutter50.4, GDM50.2, Nautilus50.2.2-1+toddy1,
LocalSearch3.11.1-1+toddy1, Gvfs1.60.2-1+toddy1, GTK4.22.4-1+toddy13.
Parent lfs-target.qcow2 identity historically before native1:52,446,887,936B,
mtime_ns1794373717214861615/device66306/inode11929205; compare actual, never trust
chat PID/state alone. Reserves target16GiB/host100GiB/scratch128MiB.

[Owned Gvfs](evidence/B02-gvfs-install.json) recipe4022 recipe/post0/0,
146changes/324entries;131original regular files/21ELFs, CLI refusal/recovery,
unauthenticated admin-helper refusal, unchanged policy/shared GIO cache.
SFTP two-file runtime omission until owned SSH client; full original stage retained.
[Owned schema union](evidence/B02-gvfs-schema-union.json) recipe4906 recipe/post0/0,
GTKtoddy13,132schemas/1113keys preserves131baseline/1111keys/contracts and906runtime
entries. CacheSHAa352c74e50964dca946948f2e80e9345a175615c938c65295f1bb44623133e1b.
Native archives retained; never replay either completed transaction.
Nautilus promotion custody1 reclaimed ONLY duplicate usr copy16,662,528B with
zero installed-root changes; original workstage/source/compiler/archive/control
retained. Never replay custody or promote retired copy.

[Generation4 custody/actual isolated restore](evidence/B02-files-trash-input-custody.json)
COMPLETE:85,958entries/42,228regular inode classes/35,017hardlinks. All prior
schema/compiler/source/stage metadata/bytes/hardlink classes unchanged. Archive
.local/phase2/settings-scratch-custody-4/scratch.tar.gz485,113,684B/SHA256
194480fde5b0e4fefd3cb947b9894150820824428a8e3245aae7ee12a5150ba9;
guest receiptSHA98d30271729661273b2824ab3d7585c944b53a59830b1cd4a5e06537c7426b4b.
Generations1-3 retained; do not replay any custody. Host110,156,697,600B free
immediately after archive, before latest native overlay. Measure current free.

For a future cold restart inspect actual stopped state,
start builder once, restore SAME6existing volume UUIDs/inodes with restore_volumes()
from virtual_discard_checkpoint.py (FUNCTION ONLY, never trim/main), same Systemd
source via prepare_systemd_pam_input.py --restore, same Glycin companion and kernel
COW using NEW receipt names. Kernel scratch remains1GiB UUID
c6c4176d-faed-4ee3-9ae0-94914a0af666; never format/resize/reprepare/rebuild.
Then phase2_restore_settings_scratch.py --generation 4 --receipt <NEW-unique-name>.
Actual archive restoration already qualified; reconcile receipt/mounts before
retry. No source/compiler/fixture/install replay. Older exact recovery identities
remain in journal, native evidence and retained receipts.

## B02 work still due

Firefox frozen browser build/install/UI; NetworkManager activation/real network;
audio session/playback/controls; affected privileged storage/device/refusal and
recovery checks; supported global navy/theme/terminal defaults respecting users;
Editor refusal/recovery/reboot persistence; offline/absent-agent operation,
minimal manifest/security-ABI review, resource/boot-idle measurements and recovery
entry boot. Preserve actual native owner Editor/Terminal/Settings and Files local
proofs; broaden only for changed inputs or final essential gates. No physical
hardware/support claim. Complete ALL B02, then STOP before another story.
