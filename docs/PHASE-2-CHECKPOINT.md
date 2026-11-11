# Phase 2 continuation card

Owner boundary: **complete ALL B02, then stop before another story**. Full Phase2
Goal incomplete. B01/B03 accepted; B02 in_progress; B04 integration blocked;
B05–B13/G2 pending. Weighted accepted Phase2 progress13%, no partial B02 percentage.
ADR0113 records authorization. Physical foundation tests unperformed. No accepted
complete GNOME/login/basic apps or Phase2 ISO exists.

## Current slice and exact next action

Current B02 slice: libbytesize 2.12 is installed and qualified for local SDK use.
[Native and staged evidence](evidence/B02-libbytesize-install.json) records recipe
and postcheck 0/0, 56 changed paths, 131 payload entries, archive SHA256
ada739b64538cf157830af8dd5421579b81eda0aeec1319526a05285970c1907.
Exact retained build and stage maps cover two ELF and 42 regular files.
Original selected tests passed 76 cases with three explicit locale skips. The
first staged Python probe failed on its exception expectation. The suffix-only
resume passed and preserved the compiler, original tests, stage and C probe.
Native C/Python/CLI refusal and recovery, byte identity, ABI and APT checks passed.
No device, UDisks service, Settings UI or physical acceptance.

The first native preflight found an incorrect archive parent path and made no
guest change. The corrected read-only preflight passed. Native PID 104803 reached
terminal success. Keep /var/log/toddy/build/b02-libbytesize-install.success.json
and its log. Never replay preparation, compilation, suffix or native installation.
[H11 ISO custody](evidence/B02-h11-iso-copy-custody.json) recovered 1,095,000,064 B
of host space by preserving both names for identical closed immutable ISO bytes.
Never replay custody. Last target free 17,209,540,608 B, scratch free
561,504,256 B. Recheck actual host, guest lock and storage before mutation.

The next dependency, libatasmart 0.19, was prepared from the frozen archive
and built with owned Systemd libudev 261. Main job libatasmart-1 PID 105525
compiled and staged, then the local C probe failed because atasmart.h uses
size_t without including its definition. Corrective libatasmart-probe-2 PID
108844 exited 0 after supplying stddef.h only for the probe. Two upstream
SMART blobs were parsed, truncation was rejected without losing the prior ATA
model, and valid reload passed. Eight ELF hashes, eight staged file hashes and
four retained logs were identical. [Evidence](evidence/B02-libatasmart-stage.json).
Guest terminal receipts are under /var/log/toddy/phase2/. Native job
b02-libatasmart-install PID 109417 reached terminal recipe/postcheck 0/0.
It changed 23 paths and installed 27 payload entries. Archive SHA256
83cd2a7cefb42fc965e15dfae85fd41c09ec44fefdf373ea47b747cf9c2aba6f.
[Install evidence](evidence/B02-libatasmart-install.json) records exact staged
bytes and links, retained five notices and full LGPL text, owned libudev/ABI/APT,
and UID 101 installed C/CLI truncated-input refusal and valid recovery.
Do not repeat preparation, compile, stage, probe or install.
Last target free 17,205,194,752 B, scratch free 561,504,256 B.

Keyutils 1.6.3 staged from the frozen libblockdev dependency. Actual compiler
job keyutils-1 PID 110728 exited 0. Stock C++ header syntax check, C shared
library metadata and installed-layout CLI version passed in the isolated
worker. [Evidence](evidence/B02-keyutils-stage.json) records 12 ELF files,
46 staged regular files and 13 staged links. Guest terminal receipt and log
are /var/log/toddy/phase2/keyutils-1.exit and keyutils-1.log. Never repeat the
source preparation or build. The canonical recipe formats the required-file set
on separate lines to avoid a scanner false positive on public package paths.
The exact prepared recipe hash remains in the job evidence. Upstream make
embeds the observed UTC build date. The isolated build tested no keyring
syscall, handler, DNS or graphical behavior.

Keyutils native transaction b02-keyutils-install PID 111355 completed recipe
and postcheck 0/0 with 75 changed paths and 84 payload entries. Archive SHA256
6d731deb44cbf3aa2cc9fef6374bdafe1e8f459b3797322d68c4acf66d40faf8.
[Install evidence](evidence/B02-keyutils-install.json) confirms exact stage
regular bytes except the reviewed conffile, 13 links with the one upstream
absolute linker alias normalized in a separate stage, APT and full upstream
license notices. Six debug rules omitted because the upstream helper echoes
callout fields and can print key metadata. Both operational rules retained
with merged-/usr path checks. Original config retained as documentation.
Installed UID 101 shared SDK and CLI version checks passed. No keyring syscall
or DNS performed. Never replay build, staging or install. Upstream kernel
suite remains pending on the intended native kernel, with synthetic keys
and disposable keyrings. The intended 7.1.8 config enables KEYS/RSA/asymmetric/
X.509 and leaves BIG_KEYS and KEY_DH_OPERATIONS unset.

Libnvme 1.16.2 is now owned and installed. Job libnvme-1 PID 112455
compiled and staged, with 36 ordinary original Meson passes and two expected
NBFT refusals. Its own C probe failed on an upstream unused-parameter warning
treated as an error. Probe-only libnvme-probe-2 PID 113368 exited 0 after
treating upstream headers as system headers and reconciling the 38 registered
test names. The 99 ELF files, 17 staged files and seven logs were unchanged.
[Stage evidence](evidence/B02-libnvme-stage.json).
Native b02-libnvme-install PID 113874 recipe/postcheck 0/0, 34 changed paths,
35 payload entries. Archive SHA256
95a240a157bf0ae0474d52b30f64afaef69d17336f130c720949489baa64b942.
[Native evidence](evidence/B02-libnvme-install.json) covers local UUID refusal,
roundtrip and MI context lifecycle as UID 101, resolved pinned dependencies,
exact payload, notices and APT. No NVMe device, fabric connection, keyring or
GUI test. Never replay completed operations. No writer remains.

[EDS custody](evidence/B02-eds-promotion-custody.json) complete. It reclaimed
33,251,328 B from the closed usr replica, with the native archive, source,
original workstage, control files and installed root preserved. Never replay.

Libaio 0.3.113 is staged. Frozen Pagure returned HTTP 404 and the verified OSU
BLFS mirror supplied bytes matching the frozen MD5. Main libaio-1 PID 114564
terminal 0. The original partcheck in the private 1 GiB tmpfs passed 18 cases,
including case 14, with one explicit RWF_NOWAIT skip. Ran only original case
21 again with its tiny unlinked fixture on builder ext4, retaining its exit 0.
Libaio-nowait-1 PID 115279 terminal 0, no other test replay. Shared-library
C probe confirmed invalid-depth refusal and two async write/read recoveries.
Original compiler and stage maps retained (26 ELF, two regular files, two
links), no outstanding AIO request in the builder.
[Stage evidence](evidence/B02-libaio-stage.json).
The two root-only ext2/ENOSPC cases are outside frozen book partcheck.
Never repeat preparation, compile, partcheck, case 21 or staging.

LibAIO native b02-libaio-install PID 115823 terminal recipe/postcheck 0/0.
It installed 14 payload entries and changed 14 paths. Archive SHA256
000508dd7cf92c29ff1c7970c9cb7f7df04d59f23fe44da37a57f2f7acc84374.
[Native evidence](evidence/B02-libaio-install.json) verifies exact staged
files and links, COPYING, ABI, APT and real installed shared C AIO with
UID 101 and a private device/network namespace. No intended-kernel test.
Do not repeat installation.

[Node.js custody](evidence/B02-node-promotion-custody.json) terminal complete.
Only the verified closed promotion usr replica was retired. Actual reclaimed
200,933,376 B, installed root changed zero paths. Exact archive, historical
receipts, original compiler/workstage and DEBIAN retained. Never replay.

LVM2 2.03.42 lvm2-1 PID 116707 terminal 0. Frozen book configure flags, own
LibAIO/Systemd SDK, 156/156 original unprivileged unit cases, stage including
udev rules and three Systemd unit definitions, local Device Mapper name
escaping/pool cycles all passed. 211 ELF files, 100 staged regular files,
167 total entries. [Stage evidence](evidence/B02-lvm2-stage.json).
The build performed no service activation or device operations. Original device
suite pending in a disposable VM. Configure warns that thin/cache tools,
VDO format tool and XFS headers are absent. Retain compiler and stage.
Last verified free 17,321,021,440 B on target. Check actual host and guest
reserves and lock before mutation.

LVM2 native b02-lvm2-install PID 123784 terminal recipe/postcheck 0/0,
165 changed paths, 176 payload entries, archive SHA256
c336dedb0dc8ad0adfe3572dfdfd39d773d0bf2bd747ab512a64a9bb3ff63264.
[Native evidence](evidence/B02-lvm2-install.json) covers all exact staged
bytes/links, installed Device Mapper C probe, libaio/libnvme/libudev ABI,
APT, three upstream notices and ten conffiles. Staged udev rules invoke
pvscan and can schedule vgchange for eligible devices. Retained upstream
rules and three unit definitions. The transaction did not activate rules or
enable units. Do not replay. Native disposable-device tests remain pending.
The intended kernel has BLK_DEV_DM, DM_MIRROR and LOOP but lacks DM_CRYPT,
DM_SNAPSHOT, CRYPTO_XTS and CRYPTO_USER_API_SKCIPHER. Preserve this gap for
encrypted-volume work without silent foundation changes.

Popt 1.19 popt-1 PID 124290 terminal 0. All 65 original nested checks
passed. The assertion checks actual nested outputs because the upstream
wrapper can return 0 after printing a failure. Local staged C unknown
option refusal and two typed argument recoveries passed. 14 ELF files,
41 staged regular files, 123 entries. [Stage evidence](evidence/B02-popt-stage.json).
The staged tests exercised only the local argument parser. Do not replay.

Popt native b02-popt-install PID 128726 terminal recipe/postcheck 0/0.
Installed local typed argument handling, unknown-option refusal/recovery,
exact staged bytes/links, upstream COPYING and APT verified.
[Native evidence](evidence/B02-popt-install.json). Never replay.

Cryptsetup 2.8.7 cryptsetup-1 PID 129236 terminal 0. Four original selected
programs passed: crypto vectors, crypto utility unit tests, argument parser,
and 155 versioned symbols. Individual vector N/A results retained.
[Stage](evidence/B02-cryptsetup-stage.json). Native b02-cryptsetup-install PID
139843 terminal 0/0, 87 changed paths, 137 payload entries, archive SHA256
09bf21b3e50781c649a5a3e7f42fe60a8b14c795129d2374fd7e1ee55cf2e83a.
[Native](evidence/B02-cryptsetup-install.json) records exact installed C and
CLI LUKS2 metadata refusal/reload with both fixture hashes preserved. No
unlock, mapping, physical device or intended-kernel acceptance. No replay.

Libblockdev 3.5.0 prepared with the pinned BLFS feature selection. Main
libblockdev-1 PID 140451 compiled/staged and passed three original no-storage
tests, then own GI probe used __file__ on a proxy object. Corrective job
libblockdev-probe-2 PID 148834 passed both actual crypto plugin lifecycle
cycles after querying the GI repository path and real Python override module.
Its collector still read the original failed probe log. Collector-only
libblockdev-collect-3 PID 149046 terminal 0 on the exact corrected log.
All 72 ELF files, 64 regular staged files and six original logs retained.
[Stage evidence](evidence/B02-libblockdev-stage.json). No daemon or storage
actions in the staged tests.
Do not repeat source preparation, main build, tests, probe or collector.

Libblockdev native b02-libblockdev-install PID 149698 terminal recipe/postcheck
0/0, 106 changed paths, 113 payload entries, archive SHA256
8a467c51fc985011edf78a9a5328904f82d72aa407f115e5546ed13ca0be5a36.
[Native evidence](evidence/B02-libblockdev-install.json) verifies exact
stage bytes, versioned conffile, installed Python/GI load/query/unload,
Cryptsetup linkage, notices and APT. No device action. Do not replay.

[Qtbase custody](evidence/B02-qtbase-promotion-custody.json) complete:
92,434,432 B reclaimed from the exact closed promotion usr copy, no
installed root changes. Native archive, original workstage and controls
retained. Do not replay custody.

UDisks 2.11.2 udisks2-1 PID 150449 terminal 2 at the optional man target:
the frozen auto configuration found xsltproc but its offline DocBook XSL
mapping was absent. udisks2-no-man-2 PID 158476 continued the retained
build with the supported --disable-man option. Daemon, ATA SMART, available
modules and GI retained. The build, all 23 original cases, stage and C probe
passed. Job 2 then exited 1 because the generated GI accessors are explicitly
not introspectable. udisks2-gi-3 PID 165234 terminal 0 after using the local
GObject property. 71 ELF, 101 staged files and nine logs unchanged across
that correction. [Stage evidence](evidence/B02-udisks2-stage.json).
The staged checks did not activate the real daemon or devices.
Do not replay source, build, tests or probes.

UDisks native b02-udisks2-install PID 165905 terminal 0/0, 122 changed
paths, 285 payload entries, archive SHA256
d42b688f1b51a49d8881c5a0123031ed229dd402a0f107c4af164c46c8494f5e.
[Native evidence](evidence/B02-udisks2-install.json) includes exact staged
policy, installed ABI/APT, conffile and C/GI under UID 101 with private
runtime/devices/network. Retained 53 upstream Polkit actions, D-Bus root
activation and Systemd service declarations. No enable links added and
daemon not invoked. A disposable native VM still needs actual mount,
authorization refusal, system-device policy and service tests. No replay.

Samba 4.24.6 official archive is frozen. Exact GNOME Settings source shows
printers links pkg-config smbclient and the About panel calls UDisks at
runtime. Samba source and its libtirpc, rpcsvc-proto and Parse::Yapp frozen
references are pinned. Do not conflate the Samba client SDK with server
activation. Full book build estimates 757 MB with tests. Verify resource
capacity and upstream build targets before transferring the larger tree.

TI-RPC 1.3.7 source preparation 1 refused the upstream absolute INSTALL
link before extraction. Preparation 2 reused the same verified archive
and omitted only that exact Automake documentation pointer under a
whole-archive identity and traversal guard. Actual libtirpc-1 PID 166785
terminal 0. [Stage](evidence/B02-libtirpc-stage.json) confirms real XDR
endian/refusal/recovery, owned MIT GSS linkage, no upstream suite supplied.
Native b02-libtirpc-install PID 171943 terminal 0/0, 92 changed paths,
96 payload entries, archive SHA256
9c4731c0cd3b777dd3559bd0d2cf279282f9b395bdaf544b56751c35b6f43c61.
[Native evidence](evidence/B02-libtirpc-install.json) confirms installed
C/XDR, ABI, exact conffiles and APT. No RPC network or GSS authentication.
No writer remains. Last target free 17,205,121,024 B. Never replay.

Frozen rpcsvc-proto 1.4.4 and Parse::Yapp 1.21 both completed isolated builds.
[rpcgen stage](evidence/B02-rpcsvc-proto-stage.json) verifies generated XDR C
against owned TI-RPC, two record roundtrips, invalid input refusal and
identical regeneration. [Parse::Yapp stage](evidence/B02-perl-parse-yapp-stage.json)
verifies all 33 upstream tests and generated parser refusal and recovery.
The first rpcgen read-only preflight failed at shell quoting, before any write.
Corrected preflight verified 33 stage entries. Native rpcgen controller PID
175011 then finished with recipe/postcheck 0/0 and 38 changed paths.
Retain /var/log/toddy/build/b02-rpcsvc-proto-install.success.json and its
step log, SHA256 d023804e9254f4a69bb52e16842af40f76872006dddd3433292098938e9698ae.
Native Parse::Yapp controller PID 175333 finished with recipe/postcheck 0/0
and 23 changed paths. Retain /var/log/toddy/build/b02-perl-parse-yapp-install.success.json
and its step log, SHA256 09e25daad6ad93897df55f9b02127b0b3f661c5ef4cc3d787eaa3ec6f4ce96e5.
[rpcgen native](evidence/B02-rpcsvc-proto-install.json) and
[Parse::Yapp native](evidence/B02-perl-parse-yapp-install.json) verify both
owned archives, installed bytes, notices and local refusal/recovery.
No guest writer remains. Never replay builds, metadata sync or installation.

Samba client scratch preparation 1 is complete. Guest boot
0933ee87-f0bc-4074-9491-8b4e6892121f, tmpfs /run/toddy-samba-client-1
mount ID 580, size cap 2 GiB. The authenticated archive has 11,719 members
and 180,563,122 regular-file bytes. Target free fell by 8,192 B and remained
17,199,251,456 B. Read-only source and writable worker aliases are
/mnt/lfs/sources/phase2/inputs/samba-4.24.6 and
/mnt/lfs/sources/phase2/work/samba-1. Durable preparation receipt is
/var/log/toddy/phase2/samba-client-tmpfs-1.json. Never replay preparation on
this boot. A cold boot loses the tmpfs; inspect actual mount and receipt
state first and use a new preparation identity if recovery is required.

Configure job 1 exited 1 before Waf due to a route-header assertion.
Isolation diagnostic passed with UID101, no capabilities, NNP, read-only
source and SDK, and no route rows. Configure 2 reached the default LDB
LMDB dependency; configure 3 reached the default ADS LDAP transport
dependency. Configure 4 passed those checks, then the upstream Python
provisioning module hit EROFS trying to generate a file in the source.
Configure 5 used the supported C-only client profile, reached the upstream
safety summary and exited 1. Actual fcntl lock probe received errno 30
creating conftest.fcntl. The mmap probe also reported EROFS. Waf runs these
executables in its read-only source cwd. No writer remains. Exact jobs and
logs are under /var/log/toddy/phase2; configure 5 PID 189229, log SHA256
c0bbbe3b22bbe0ac4243ec597a412751413961d6ac1f5c2e5048d94df299ff8f.
The persistent failure ledger and both exact compressed log bundles are
under .local/phase2. Never replay preparation or configure attempts 1–5.

Read-only patched source preparation completed with an exact one-file diff
across 12,530 entries, original source unchanged. The Waf executable-probe
cwd correction is .local/phase2/samba-waf-configure-probe-cwd.patch, SHA256
16a878f86250475c1dc8b3eb2005f0111468269a49e812f7a0438f1a9c47f60c.
Guest preparation receipt samba-client-probe-cwd-1.json is complete.
Configure 6 PID 194911 exited 0. Runtime probes set HAVE_FCNTL_LOCK,
HAVE_OFD_LOCKS and SUMMARY_PASSES, and MIT Kerberos 1.22.2 was detected.
Original mmap EROFS diagnostic disappeared after the scoped cwd change.
Configure log SHA256 6080aaf42418f90828b10e959c5454edaf546ed95fed1ad352ff7cc6ea994214.
Do not replay configuration.

Build client 1 PID 200097 exited 1 at PIDL_ADS: source3/librpc/idl/wscript_build
hardcodes the source-relative config.h include path. Exact first build log
SHA256 7aac1ef294802d5450d8cb8b7c62f0d16c37c35d612cc118f17684dacb0d4f48.
A separate read-only alias was prepared with the second one-file patch,
SHA256 436ed956a3953cfc4e434e172a58cc8a38df4fcaa80420d68253ec0ce963f3cf.
Guest receipt samba-client-pidl-cwd-1.json is complete. Current alias
/mnt/lfs/sources/phase2/inputs/samba-4.24.6-pidl-cwd and same work alias
/mnt/lfs/sources/phase2/work/samba-1.

Build client 2 PID 203119 exited 1 after passing the affected PIDL tasks.
The generated version.h existed under output/default, one level below
Waf's launch directory. Build client 3 PID 203848 launched from that exact
directory and generated the public version header, then exited 1 at the
public SAMR header. Its generator emits an absolute build-tree include;
the public header mapper recognizes only the relative bin/default prefix.
Exact build 3 log SHA256
03fb31487ca7dff4aac1707fa503c1ccfd5e32bf8751c3487a4cfa07d14447fb.
Configure and build receipts/logs are under /var/log/toddy/phase2 and in
.local/phase2/samba-configure-and-build-logs-3.tar.gz. No writer remains.

EXACT NEXT: verify an exact build-root normalization for generated public
header includes, preserving existing lookup and refusal for all other
absolute includes. Qualify the change on the actual generated SAMR header
before dispatch. Reuse the same Waf configuration and incremental objects.
Check the persistent ledger and retain all three terminal failures.
No package, SMB runtime or Settings acceptance yet.
Cold native tests require measured headroom and an isolated VM. UDisks policy,
Settings/Samba and GNOME session remain pending. Stop after accepted B02.

### Previous Settings prerequisites

MIT Kerberos1.22.2 OWNED/local SDK accepted, ADR0215.
[Install](evidence/B02-mitkrb-install.json): native recipe/post0/0,190changed
paths,209payload entries, archiveSHA b34b8d324dd82680ea50c0ddfa6db4d649d7c807f9b73e6d39b2fe75983924c1.
Actual UID101/no capabilities/NNP/private-device/no-route local principal/MEMORY
cache/reopen/destroy/realm+absent-principal refusals/two recoveries, CLI versions/
absent-cache refusal/recovery, exact payload/ksu0755/ABI/PC/APT passed. No realm/
network authentication/tickets/daemon/login/Settings GUI/physical acceptance.
[Aggregate](evidence/B02-mitkrb-stage.json) retained897ELF/132stage maps and7logs;
metadata4 and native installation complete, NEVER replay. Scratch promotion/output
prepared once; all original source/compiler/test/stage/archives remain retained.

Native qualifier read-only assumption failures were parked after2failed corrections.
Actual command-vector3host tests qualified missing correction; ONE logged bounded
qualifier extension passed before first native installation. Historical budgets
retained. No compiler/source/test/stage/API replay of accepted build evidence.

CUPS2.4.19 OWNED native local SDK/payload accepted, ADR0218.
[Install](evidence/B02-cups-install.json): native2 recipe/post0/0,927changed paths,
964payload entries, archiveSHA01aa732dba3a9f3afa2c65b221d940808ec965a41b171a8cdcd6f1b6b5cf5e52.
Actual installed UID101/NNP/caps0/private-device/no-route IPP/refusal/two recoveries,
CLI version/paths/private-config refusal/recovery,250ELF/846stage bytes/14specific
ownership paths/locked lp9:9/empty lpadmin19/conffiles/ABI/PC/APT0. Units installed,
not enabled/activated. No printing/server/TLS/network/device/Settings/physical claim.

Factory identities use owned Shadow tools; systemd-sysusers binary absent. First
native1 failed unsupported -K CREATE_MAIL_SPOOL option after creating only group19:
exact4group/gshadow paths changed, lp9/stage/archive absent. Defaults already=no.
Unique account2/native2 source-backed resume verified exact old state/diff, omitted
-K, did NOT rerun groupadd; both historical receipts/failure retained. Accounts2
complete; NEVER repeat accounts/native install. Archives have no maintainer scripts;
audited base factory account setup is required before arbitrary-root acquisition.

[Librsvg custody1](evidence/B02-librsvg-promotion-custody.json) COMPLETE/root0,
reclaimed30089216B from only closed promotion usr; all source/compiler/workstage/
archive/DEBIAN retained. Prior QMI/MIT/GWeather custody complete; never replay any.
Corrected source jobs/legacy wrong-prefix and first reserve failure remain in
[stage proof](evidence/B02-cups-correct-layout-stage.json). No compiler/test/stage
replay in native acceptance. Generic harness unchanged, cold worker restore untested.

Receipt repair1 COMPLETE, [proof](evidence/B02-mitkrb-worker-receipt-repair.json):
preparer prerequisite-variable shadow misplaced MIT worker JSON over Libgtop
success receipt. Actual worker record relocated; original Libgtop success bytes
restored from retained controller output, exact pre-existing SHA2566c32a0e6bf67b13e27ae083f2d085a6ec0c03cb71a60138963db52f3699f6c45.
All3 preparers fixed and worker namespace guarded. No package/source/compiler
replay, no lost installed package; NEVER repeat repair1.

Previous handoff: frozen UDisks2.11.2 Settings prerequisite.
Read .local/books/blfs/general/udisks2.html and general/libblockdev.html (3.5.0),
then only their required selected closure/current owned package state. GNOME
Control Center frozen page lists UDisks2.11.2/Samba4.24.6 as required.
UDisks/libblockdev exact official archives are cached/SHA-pinned after frozen
MD5/header-path validation, [source proof](evidence/B02-udisks-source-preflight.json).
Historical source-only handoff. Current storage and Samba state is recorded above.
Inspect the required selected transitive closure and existing owned libraries;
then prepare one missing eligible leaf. Preserve core Settings panels, no silent
dependency/feature disable or foundation upgrade. CUPS filters/printing is not a
blanket new mandatory hardware matrix for this local SDK slice.

First inspect actual Git/lock/jobs/mounts/resources. Last targetfree17215127552B
(35,258,368B above16GiB), scratch561504256B (24,633,344B above512MiB). A fresh
UDisks build will need further verified closed-promotion headroom; source/compile/
workstage/archives remain retained. Read-only candidate inventory is local; Node
bootstrap/Qt/GTK/hwdb promotions are candidates only, not prequalified deletion.
Never lower reserves, replay custody/native install, or overwrite uncertain state.
Actual builder boot0933ee87-f0bc-4074-9491-8b4e6892121f; native2 terminal0/0.
Complete ALL B02 then stop before another story; full G2/ISO and physical tests pending.

Seven qualified Settings prerequisite archives/metadata copied and independently
verified outside VM: [recovery cache proof](evidence/B02-settings-package-recovery.json),
.local/native-package-snapshots/settings-owned-1/state.json COMPLETE7packages,
6133760B tar SHA8b34b98b537d2bf8b902d19c66da034b80014b5e5f10d462ddc557756cba5026.
Only a partial native-package recovery cache, NOT a bootable/full system checkpoint
or release. Do not repeat export; verify inventory/archive hashes before recovery.
Original VM source/compiler/stage/raw failures/archives and all scratch binds remain.

GNOME Bluetooth47.2 source/compiler/stage/native install COMPLETE,
[stage](evidence/B02-gnome-bluetooth-stage.json)/
[install](evidence/B02-gnome-bluetooth-install.json):115ELFs/101files,
original2programs5cases passed,15private-bus integration programs compiled/deferred.
Native recipe/post0/0/119changes; actual installed C UI header/type query only
(no widget instantiated), core GI address/classification/shared ABI/APT0 under
UID101/NNP/private-dev/no-route. No adapter/pairing/transfer/UI/physical acceptance.
NEVER replay preparation/source/compiler/tests/stage/install. No live writer.

Private scratch preparation COMPLETE, [receipt](evidence/B02-bluetooth-scratch.json):
new worker inode2215 inside existing Doxygen scratch
UUIDae4347fb-31fd-4193-a333-0a549e144231. Original cache manifest and GSound bytes
unchanged. Future cold restore must first restore Doxygen, then updated existing-
bind helper binds this SAME optional Bluetooth subtree with the original three
editor workers. Never recreate/replay/format/resize or run old restore contexts.

GSound1.0.3 revision2 COMPLETE, [stage](evidence/B02-gsound-stage.json)/
[install](evidence/B02-gsound-install.json). Original native1 wrong libcanberra
exact revision left unpacked; actual qualified library is0.30-1+toddy2. Controlled
metadata-only package2 upgrade installed (source/compiler/stage bytes retained),
own direct GObject/GIO linker flags corrected in verify-only3/post0/0/root0.
Actual installed UID101/NNP/private-dev/no-route null backend properties/disabled
refusal/two recoveries/GI type/CLI help-empty refusal/APT0. No original suite,
not a pass; no audible/device/Bluetooth/Settings UI acceptance. NEVER replay.

Control Center Linux conditional source confirms BOTH ModemManager mm-glib and
GNOME Bluetooth UI mandatory. Versions1.24.2/47.2 frozen; GSound is the latter's
required predecessor. Do not disable Linux panels or misreport complete Settings.
Control Center expanded49149703B exceeds target headroom; use existing scratch
source+worker for that later build, preserve16GiB/100GiB reserves. ModemManager is now installed as recorded above; Control Center guest source/job remains absent.

Cracklib2.10.3 COMPLETE, [stage](evidence/B02-cracklib-stage.json)/
[install](evidence/B02-cracklib-install.json): two original programs20ELFs/67files,
full recommended1930240line dictionary source compressed/expanded hashes fixed;
native recipe/post0/0/84changes. Actual installed default-dictionary C API weak/
missing-dictionary refusal/two recoveries/no-echo CLI/APT0, all stage bytes retained.
Exact raw wordlist remains compressed with verified custody; packed indices installed, provenance and
original notices retained. No arbitrary external wordlists/owner password use.

Libpwquality1.4.5 COMPLETE, [stage](evidence/B02-libpwquality-stage.json)/
[install](evidence/B02-libpwquality-install.json):12ELFs/66files; no original suite
(NOT a suite pass), native recipe/post0/0/80changes. Installed C API/CLI synthetic
weak/invalid-setting/empty-input refusal/two recoveries/ABI/APT/conffile0.
All12active PAM files unchanged; module packaged but inactive, authentication
unqualified. ADR0208 and [bounded review](evidence/B02-libpwquality-security-review.json)
retain empty public advisory observation without a no-vulnerabilities claim.
Never repeat either source/compiler/tests/stage/install transaction. No live writer.

GOA3.58.1 native install+verify COMPLETE, [proof](evidence/B02-goa-install.json).
Initial recipe0/post1/135changes retained (own GI method assumption); installed
GIR-backed writable-property correction verified recipe/post0/0/changed0. Actual
UID101/NoNewPrivs/private-dev/no-route version/invalid-option refusal/local GI
Unicode skeleton+two resets/no account files/shared ABI/APT0. No real session daemon/
account/provider/secret/Settings/GUI acceptance. NEVER reinstall or repeat verify2.
No live guest writer. Host runtime/failure ledger records resolved corrections.

GOA compiler/stage/version succeeded; initial own collector expected Meson define1
instead of actual bare define. Metadata-only collection2 PID4460 terminal0 verified
all compiler/stage entries unchanged, [proof](evidence/B02-goa-stage.json).
Never repeat source/compiler/stage/version.45ELFs/116stagefiles, no original tests
registered (NOT a suite pass). Core/backend/GI/Vala enabled. Google/Microsoft365
unavailable and shared app IDs empty, ADR0207; Kerberos/Fedora unselected.
Cracklib/libpwquality later completion is recorded above; never change host PAM/account policy.

Librest0.10.2 install PID3105 TERMINAL COMPLETE, native recipe/post0/0/49changes,
[proof](evidence/B02-librest-install.json). Installed C/GI Unicode XML/nonXML
refusal/two recoveries/local proxy construction/shared ABI/APT0; stage unchanged.
Seven original local programs plus original Flickr URL-only case passed;
[stage](evidence/B02-librest-stage.json). External-service cases unexecuted.
DO NOT repeat source/build/test/stage/install. ArchiveSHA
7ab19965a1b30f1b77da2ce9fbb723208e219a4e99fd07fe02a388338cff08db.

Tecla50.0 native CLI1 COMPLETE/PASSED, [proof](evidence/B02-tecla-native-cli.json):
actual7.1.8/Systemd/Mutter --version/help0,2975artifacts unchanged, container0/
OOMfalse/backing unchanged. Native package install/post0/0/67changes,
[proof](evidence/B02-tecla-install.json), exact installed stage/PCapp/ABI/APT0.
No keyboard preview GUI/input acceptance and no registered upstream test passes.
Host context .local/phase2/native-tecla-runtime-1 and builder recovery1 COMPLETE;
six original volumes/Systemd/Glycin/kernel/editor binds restored once. DO NOT
replay CLI/source/compiler/stage/install/recovery1. CLI report bound by canonical
protocol digest (formatted JSON digest is separately recorded).

Exact-path LocalSearch bus qualification branch also PARKED after two corrective
failures; no native functional LocalSearch4 dispatched. SDK2 own token substitution
SyntaxError before daemon, SDK3 chroot cwd reset before daemon, SDK4 selected
readonly cwd but /dev/null placeholder denied: root-owned regular0644 file in
builder's unbooted target, not a private device binding. No global device chmod/
creation or permission relaxation. [Failures](evidence/B02-localsearch-private-bus-failed.json).
All original770source/403compiled/133stage files rechecked unchanged. Failed own
producer sources/logs retained, replay guard now checks failed log before operation.
No SDK5 until independent qualified private-device profile and bounded reopening
retaining history. Original isolated bus-address proof1 remains valid in its own
qualified profile only; no functional/search/extractor/package acceptance.

Independent eligible Settings preflight source50.4 verified: Tecla/pwquality/GOA
required and absent; GTK/Adwaita/NM/Accounts/UPower/desktop libraries owned. Use
pinned Tecla50.0 instead of moving wrap HEAD, no online-account/provider credential
or mandatory hosted backend. Do not silently disable core settings to pass builds.

Editor graphical branch PARKED after two failed corrective native runs.
Native4 overall FAILED: first real open/mapped/active/focus/UTF8 edit and exact save
predicate were reached, then test capture(saved) returned no render node. No normal
close/reopen/resize pass. [Failure/partial proof](evidence/B02-editor-native-failed-4.json).
Two actual920x640 client PNGs decoded/visually reviewed: readable controls, UTF8
filename/text/caret and changed modified-dot; no visible clipping in wide state.
[Opened](evidence/screenshots/B02-editor-native-opened.png),
[edited](evidence/screenshots/B02-editor-native-edited.png). These are the unmodified
installed editor, not fixture UI/mockups. Programmatic GTK actions/real compositor
virtual input, not physical keyboard/full GNOME/GDM or hardware acceptance.
Actual saved document artifact removed by fixture cleanup: save postconditions are
explicitly derived from executed immutable driver3 branch guards, not a fabricated
standalone report. GIO cursor metadata unsupported; persistence unqualified.

DO NOT launch native editor5 or reset budgets. Unblock only after independent
source-backed GTK snapshot/frame readiness qualification with real runtime evidence
and an explicit bounded reopening retaining both failed corrections/history.
Source GtkSourceView5.20.0 implicit-newline contract now confirmed at runtime;
property/defaults untouched. Product binaries/packages never rebuilt for fixtures.
Native1 was preboot transport failure; native2 old bare-seat/text expectation wait;
native3 mapped/active but wrong terminal-newline expectation; native4 saved then
capture synchronization failed. All raw reports/failed attempts retained.

Native4 container terminal0/OOMfalse/backing unchanged, NOT a full GUI pass.
Restoration4 COMPLETE (.local/phase2/editor-builder-recovery-4.json and guest
editor-builder-restored-4.json), same six volumes/Systemd/Glycin/kernel/three editor
binds restored; no replay. Editor restoration was complete before the later Tecla/librest jobs. All native editor/GTK9/cache/
discard/custody/install/source/driver compile operations are complete, never rerun.

GNOME Text Editor50.1 OWNED nativePID30824 recipe/post0/0/376changes,
archiveSHA77ce94f6eccd6403c99fa6d7c3293aa080e5d0cf3ecec7e8def687fc6f9c2dec.
[Install](evidence/B02-gnome-text-editor-install.json). Shared GTK4.22.4-1+toddy9
strict union preserves115schemas/900keys, installs editor+five terminal schemas,
actual121schemas/1057keys matched; noncache/nonlegal payload unchanged.
[Cache](evidence/B02-editor-schema-union.json). NEVER replay either transaction.

ICU/Doxygen duplicate promotion custody1 COMPLETE PID31236,
78950400B reclaimed, installed root0 and both original workstages unchanged.
[Proof](evidence/B02-editor-cache-stage-custody.json). Only closed promotion usr/
etc copies removed after archive/payload/installed bytes verified. Original cache,
source/compiler/stage/raw/native archives retained; NEVER replay retirement.

[Editor stage proof](evidence/B02-gnome-text-editor-stage.json): main1PID29209
compiler/stage/version succeeded, own zero-test collector assumption failed.
Metadata2PID30174 terminal0 ran first actual original offline AppStream metadata
test and collection only; no compiler/stage/version replay. Stage/artifact hashes
independently verified. Original source/recipe remain immutable in builder.

EditorConfig0.12.11 now OWNED: [proof](evidence/B02-editorconfig-install.json).
Original202CTest cases + installed C API/CLI layered UTF8 settings, relative-path/
malformed-config refusal/input retention/two recoveries passed. NativePID28171
recipe/post0/0/26changes. ArchiveSHA
 a0803a62f0d5e857c62b97fbbfb84423f3f0f7f6776c3e6d3479a3b351f600ed.
Never replay original source/build/tests/stage/native install. Source and exact
original tests gitlinks retained in source lock; frozen PCRE2 reused, no upgrade.

Shared preallocated Doxygen scratch UUIDae4347fb-31fd-4193-a333-0a549e144231 now
also holds independent editorconfig-1 inode1011 and gnome-text-editor-1 inode1157
under toddy-editor-workers, bound to corresponding direct work mountpoints.
Preparation receipts COMPLETE, no allocation/format/resize/original cache changes.
After a cold builder restore verify same Doxygen UUID, each worker inode and empty
unmounted target, then bind SAME subtree; never recreate/replay preparation.
Libspelling worker inode489 is also retained. Isolated source/read-only installed
dependencies remain unchanged; each sandbox exposes only its own private subtree.

Cargo-c duplicate promotion custody1 COMPLETE: PID28623 reclaimed165642240B,
installed full-root changed0 and original workstage unchanged. Installed payload,
retained native archive and duplicate matched before removal. Only promotion usr
retired, DEBIAN/original source/compiler/stage/raw/native archive retained.
[Custody](evidence/B02-cargo-c-stage-custody.json). NEVER replay. After custody
actual free17356251136B, before subsequent editor source extraction; check actual
free before transaction. No reserve reduction or physical storage operation.

Libspelling0.4.11 OWNED, native PID26455 recipe/post0/0/87changes,
installed Spelling1 GI/refusal/ignore/recovery/UID101/NoNewPrivs/private-dev/no-route/
APT0 passed. [Installed proof](evidence/B02-libspelling-install.json).
ArchiveSHAa889dd3c9442e2583d08bfcc6c2af5d71cac088c5a96a2629a69340bcc5b7ff5.
Never replay source/compiler/tests/stage/native transaction.
[Stage proof](evidence/B02-libspelling-stage.json): first build compiled library/
original tests/GIR, optional Vala failed because owned GtkSourceView has no VAPI.
Supported vapi=false matches C/GI consumer; options2 terminal0, original ELFs
unchanged, four original programs21cases and staged real Spelling1 GI consumer
passed. No original test/compiler/stage replay. Source SHA
52e53ec3fba0f604cfd0931e26af7f7241a0d4f0208dd5574f43b3589f6d28b2.
Original recipeSHAdac22957acb37eed94860df8a2d6b5d4ed2ad19639ac9bef2b0ca975de833ffc.
Raw collector prose incorrectly retained Vala-enabled wording; qualifier explicitly
annotates actual Meson vapi=false without rewriting raw evidence. No GUI claim.

Shared compiler scratch1 COMPLETE: existing Doxygen UUID
 ae4347fb-31fd-4193-a333-0a549e144231, new private subtree
/mnt/lfs/sources/phase2/work/doxygen-1/toddy-editor-workers/libspelling-1 inode489
binds onto /mnt/lfs/sources/phase2/work/libspelling-1. No new allocation/format/
resize or deletion. Original Doxygen manifest unchanged. Scratch ~1.1GiB free,
independent256MiB compiler reserve; target16GiB/host100GiB reserves unchanged.
NEVER replay prepare_libspelling_shared_scratch.py. After a cold builder restore,
first restore existing Doxygen mount/UUID, verify worker inode489 and empty target
mountpoint, then bind SAME subtree; no recreate. Receipt
/var/log/toddy/phase2/libspelling-shared-scratch-1.json contains identity/recovery.
Native space preflight stage822141B/free17194676224B/required17190724215B passed.

Completed prerequisite: Enchant2.8.19 OWNED and installed.
[Installed proof](evidence/B02-enchant-install.json). Native PID24124 recipe/post0/0,
31 changed paths, actual installed UID101/NoNewPrivs/private-dev/no-route API+CLI
consumer passed, all15staged regular files identical/APT0. ArchiveSHA
b2e49f57d83eaaef1097d105dee89808abf3f5c8c7801050f225dfc4af06a6f5.
NEVER reinstall; no Enchant compile/test/stage replay.
[Proof](evidence/B02-enchant-stage.json). Job5PID23286 terminal0; original
SDK267/main432/explicit real Aspell provider25cases passed, all current compiled
and staged hashes independently matched. Default provider scan zero cases is NOT
a pass; four upstream CLI scripts unexecuted. Own staged API/CLI English dictionary,
UTF8 personal persistence/session/refusal/recovery passed; no editor/GUI acceptance.
SDK remains private build-only. Source SHA
c8d70991d544ee39274b96bd01d2858a009fe732ff43f2aaf605fd61ecd06f60.
Original recipeSHA c2c74aba728c71cffe61a1ce11a5e0facf827b75417dd88593fd7a9cbec4aeab.
All five job results and exact correction payloads retained; no build/test/stage replay.
Recovery4 accidentally overwrote failed header-compilation stdout3: preserve this
limitation, actual exit/resource record and separately labelled observation; do not
claim reconstructed raw output. Raw archive SHA
eaf9d9679e8d79d024c4d6a67bce0c0bf882c51198b981eab2cbd52b9ccd579f.

Aspell installed/qualified, no reinstall. Duplicate promotion stage custody1 and
Tinysparql/Exiv2 custody1 COMPLETE, NEVER replay. Original source/compiler/workstage,
archives, installed payload and raw evidence retained; full-root changed0.
[Custody1](evidence/B02-aspell-stage-custody.json),
[custody2](evidence/B02-editor-dependency-stage-custody.json).
Aspell Info inventory metadata correction COMPLETE; original package/index unchanged,
[installed proof](evidence/B02-aspell-install.json), ADR0206.

Actual last target free17195585536B, reserve17179869184B. Enchant native preflight
required17189013630B and passed; transaction complete. Libspelling was subsequently built/installed above. Preserve target16GiB/host100GiB margins. EditorConfig remains
required for selected editor. No live writer; builder boot9d54ab78-a01a-428b-86e9-6055effef25b.
Full B02 then stop, not full Phase2 completion.

Editor [SDK preflight](evidence/B02-editor-sdk-preflight.json) is historical before
Aspell installation:7owned modules found; Enchant/Libspelling/EditorConfig absent.
Editor50.1 sourceSHAf68036b09d378faa883bfe936e479c6ff37027c2ffed101daf912df70c51d0e6,
Libspelling0.4.11 SHA52e53ec3fba0f604cfd0931e26af7f7241a0d4f0208dd5574f43b3589f6d28b2,
Enchant2.8.19 SHAc8d70991d544ee39274b96bd01d2858a009fe732ff43f2aaf605fd61ecd06f60
selected/verified. Aspell and English rows/license notices frozen. Include actual
EditorConfig dependency instead of silently disabling default editor support.
No live guest writer/native child. Complete ALL B02, then stop.

## Parked LocalSearch functional branch — do not repeat

[Build](evidence/B02-localsearch-build.json) remains accepted compile/stage only:
186ELFs/133stagefiles,13original non-slow basic programs0,72registered not executed.
Build1PID26113 terminal1 only own macro collection; collection2PID27647 terminal0.
Original source recipeSHAf25eb13e03a5b1fde6763e0bea50e923bec82ebae12cbc596d0cbb2e060d2499
immutable. No source/compiler/accepted-test/stage/prepare/collection replay.
Fixture1 root-owned166741B descriptorSHA
bcd521657ff4861f3ca9391c045d1d6bf03f2bf0f9e8e1907db5fae0e68a01fe binds
770source/403compile/133stage files,9programs/20expected cases. Both receipts
/var/log/toddy/phase2/localsearch-native-fixture-1.json and
/mnt/lfs/sources/phase2/native-fixtures/localsearch-1.json complete; never republish.

Actual native attempts1/2/3 all TERMINAL FAILED, full reports/raw preserved:
[1](evidence/B02-localsearch-native-failed-1.json),
[2](evidence/B02-localsearch-native-failed-2.json),
[3](evidence/B02-localsearch-native-failed-3.json).
All installed7.1.8/Systemd, containers exit0/OOMfalse, backing+input hashes unchanged;
these are NOT functional passes.1/2 first search insert timeout10s,3 private bus
socket EROFS before miner startup. Corrective attempts2/failed2: PARKED. Do not
run fourth attempt or reset budget. Cause1 own TMPDIR overlap corrected; insufficient.
Private GSettings diagnosis1PID1447/exit0 disproved missing-DConf hypothesis; no
module override added. Source showed BUILDROOT cwd needed for extractor/helper/
Landlock in-tree rules. Correction2 restored original Meson cwd with compiled
inputs readonly and ONLY generated TEST_ROOT redirected to private ext4. Original
bus config unix:tmpdir=./ then tried socket in readonly BUILDROOT and failed.
Unblock only after independent source-backed private writable bus-address
qualification preserving isolation; record a bounded reopening with historical
budgets intact. Current eligible independent editor branch above.

Last native3 controllerPID294671/context .local/phase2/native-localsearch-runtime-3,
container40696bf6c6ad7487f78ba8293bb1d626846a84e8d993b59aadb52ae66dda8148
exited0/OOMfalse, reportSHAf91bb7f44294b292cb6b12af1781173227d1f4dfa45298da7b1469796630fa4c.
Builder restored after3: boot9d54ab78-a01a-428b-86e9-6055effef25b.
localsearch-builder-restored-3.json, kernel-work-restored-localsearch-3.json and
companion3 COMPLETE; same six scratch/Systemd source/kernel UUID+inodes. No
format/resize/rebuild. NEVER replay any restoration1/2/3 receipts. No live writer
or native child. Source/build/report/raw hashes and explicit failures remain in
linked proofs. Recovery-entry boot, installed package promotion and GUI pending.

## Recovered host headroom

New byte-exact custody generation2 compressed30 actual stopped/owned test overlay
files,441909248B allocation reclaimed, all raw bytes recoverable. Post-commit
metadata sync+preflight1/2/3 actual free stayed>=100GiB+512MiB; no guard reduction,
trim replay or uncertain write. [Custody](evidence/B02-native-overlay-custody-2.json)
ledger .local/phase2/native-test-overlay-custody-2.json COMPLETE; never replay.
Old headroom failure budget retained; new native failures are functional fixture
failures. Recheck actual resources before any future native dispatch, not repeated
cleanup. Gzip restoration requires archive and decompressed-source hashes from
ledger; old test deltas must not be booted against a changed mutable backing.

## Completed native kernel and boot owner slice

[Native package evidence](evidence/B02-kernel-native-packages.json): archive build
PID23664 recipe/post0/0/full-root changed0, complete actual tar12027entries/modes/
ownership/rollback QA. Kernel installPID24136 recipe/post0/0/full-root12changes,
linux-kernel7.1.8-1+toddy1 installed, full payload/ownership/APT0 and original
archive/three rollback image artifacts retained. ArchiveSHA
75f0acd71dc1e8f3d66fcd0f6ce70f1f201bd1b7c9344296240175742c65714f.
Separate toddy-boot-config0.1-2+toddy1 installPID24572 recipe/post0/0/full-root6changes,
default0 plus foundation recovery entry/source/syntax/ownership/APT0 verified.
ArchiveSHA3e722231aa65f780775c74b1c47af66868dc34ff83f8d55525c68078e1d65cbf.
NEVER replay archive build/kernel commit/boot config update/staging/diagnostic boots.
Installed main kernel actually reached native7.1.8/Systemd in LocalSearch attempt1;
functional test failed for own TMPDIR fixture. Recovery-entry boot still pending.
Candidate imageSHA18c4d9e6a64554296d8e9a037c2383e7426a0cf155b6d757d0693fce0d087ad1;
[earlier actual BIOS/UEFI diagnostic proof](evidence/B02-kernel-landlock-native.json)
ABI9/UID101 allow-deny/recovery/seccomp/namespaces/module0,20modules byte-identical.
This proves diagnostic kernel behavior, not installed Systemd/GNOME/recovery entry.

Kernel stage source W/stage normalized root, DEBIAN control exists; completed
bind alias /mnt/lfs/sources/stage/phase2-linux-kernel-landlock. Do not repeat the
pre-pack qualifier on this now-promoted stage. Native old and new archives retained.
Boot conffile belongs only to toddy-boot-config, /etc/toddy/grub.cfg with
/boot/grub/grub.cfg→../../etc/toddy/grub.cfg. Original owner config matched H09
before update; local edits were not overwritten. Next actual cold tests must
verify default plus selected foundation recovery entry and source base unchanged.

## Historical resource branch and verified custody recovery

Native cold runner requires100GiB+512MiB host free. New virtual /dev/vdb4 free-
block reclamation1 actual0, installed160864entry OS snapshot unchanged and original
111558entry/2599875499byte kernel cache unchanged. No files deleted/physical trim.
Receipt kernel-transaction-discard-1.json COMPLETE; compressed private pre-snapshot
kernel-transaction-before-full-1.json.gz kept in builder log. NEVER replay trim.
A later input sync was followed by renewed shortfall: recorded hostfree
107675385856B <107911053312B gate. That attempt did not unblock it; guards remained unchanged.
Input transport now reuses verified identical files and uses existing /run tmpfs
for metadata-only staging. Actual idle sync0 reused1735/replaced1; hostfree
107666182144B unchanged across this measurement. Nine focused integrity/path/cache
tests0; [proof](evidence/B02-input-sync-reuse.json). This prevents unnecessary
rewrites; that input-transfer change alone did not resolve the shortfall.
The later generation2 custody above restored measured headroom and allowed
actual native attempt1, without attributing earlier space changes to one cause.
Failure ledger installed-kernel-boot-host-overlay-headroom persists, correction1
failed to sustain headroom; diagnosis budget parked. Advance independent eligible
LocalSearch build preparation. Reopen only with concrete new cache/input-transfer
custody evidence and bounded logged extension, not a fresh budget after compaction.

restore_kernel_landlock_work.py first actual cold restoration passed after LocalSearch attempt1;
read-only --inspect passed current mounts (upper inode14/work15/lower7523763).
Actual cold restore qualified in kernel-work-restored-localsearch-1.json after native attempt1. It mounts same1GiB UUID and
existing private COW only, never formats/resizes/extracts/chowns or replays builds.
Completed native-stage alias intentionally need not return after cold recovery;
archive/payload already qualified and stage data retained at W/stage. No guest
writer or native diagnostic VM currently active. Full B02, then stop.

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

Current boot9d54ab78-a01a-428b-86e9-6055effef25b; target
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
receipt names, then same Glycin companion. Kernel scratch restoration helper above actually qualified after LocalSearch attempt1; same UUID/no mkfs/resize/preparation/chown replay. Native diagnostic above does NOT stop parent or share its disks.

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

Last published0f7a9b8b37abde74fe30b19b8e9ec29351914d7c: all3CI success,
exact publicHTTP200/indexSHA
45429c1058a5a2277b66a7267ba52d4cfad3ddb9f36fd07c4cf7fb88365dcaa1.
