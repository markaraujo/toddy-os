# Phase 2 continuation card

Owner boundary: **complete ALL B02, then stop before another story**. B01/B03
complete, B02 in_progress; B04 final integration blocked, B05–B13/G2 pending.
Weighted Phase2 progress13%. ADR0113 records authorization before B01. Physical
foundation tests remain unperformed. No complete GNOME/login/apps or Phase2 ISO.

## Current slice and exact next action

Current slice: next GLib TLS/proxy prerequisite preparation. No active writer;
`b02-ca-native-install.success.json` and `b02-gnutls-install-2.success.json`
both prove recipe/post0/0. CA data changed717paths,721owned entries, all9803
OpenSSL package entries unchanged. Actual installed default P11/GnuTLS/OpenSSL
trust and legacy aliases pass. GnuTLS changed66paths; installed library/SDK/
crypto/UTF8/IDNA/priority/refusal/recovery and unchanged original trust program0.
[Decision/evidence](adr/0164-real-system-trust-and-gnutls-integration.md).

GnuTLS retains917distinct original records:813PASS/102SKIP/two original FAILs.
Certificate list80entries includes seven duplicates,73unique PASS driver records;
own stage4 count corrected in stage5 without test replay. First native qualifier
failed only ordered enumeration comparison, ZEROroot changes/no promotion stage/
archive. Install2 compares exact917name/result maps. NEVER replay successful
CA preparation/generation/finish/acceptance/native install or GnuTLS stage/install.

Exact next: prepare frozen libproxy0.5.12 build/probe, then GLib-networking2.80.1
using owned GnuTLS and existing gsettings-desktop-schemas50.1/Duktape2.7.0.
Libproxy source cached/verified; no guest preparation/build yet. GLib-networking
source cached, no recipe/guest build yet. Use one isolated compiler writer and
private loopback for actual local TLS peers. Public DNS remains FAILED/unqualified
until actual native network. P11 callback/local trust update/recovery/NSS shared
root alias are pending controlled follow-ups, never claim them operational.
Fresh combined trust/GnuTLS build recipe portability remains pending; preserve
historical exact-input jobs and finishing helpers. No Phase2 ISO/native desktop.

Then glib-networking/libsoup/EDS and remaining GNOME/GDM/apps/network/audio/offline/
focus/responsiveness/resources. Shared caches/trust integration below remain gates.

## Latest verified boundaries — reuse, never rebuild/reinstall/retest unchanged

- libidn2 2.3.8-1+toddy1 OWNED/install/post0/0 changed69paths; all15original programs
  passed,78ELFs retained. Installed UTF8/punycode/nontransitional/invalid UTF8/
  leading-hyphen refusal/recovery/SDK/APT0. [Proof](evidence/B02-libidn2-install.json).

- Nettle4.0-1+toddy1 OWNED/install/post0/0 changed99paths;122original crypto passes,
  one upstream x86-ibt SKIP,691ELFs retained. Own v3 digest-call compilation error
  fixed consumer-only2 for v4 API; originals/stage unchanged. Installed SHA256/
  Hogweed P256/zero-scalar+off-curve refusal/recovery/SDK/APT0.
  [Proof](evidence/B02-nettle-install.json).
- libunistring1.4.2-1+toddy1 OWNED/install/post0/0 changed65paths;638original passes/
  36skips,1905ELFs retained.33Windows-only, two network-dependent select/pselect
  (isolated route unavailable), one absent traditional Arabic locale. No skip is
  a pass. Own initial assumption that normalizer rejects malformed input failed;
  source uses unchecked decoder, documented validator is u8_check. Corrected
  consumer-only2 validates first, never passes malformed input to normalizer.
  Installed UTF8/NFC/Portuguese case/refusal/state/lifecycle/dynamic SDK version/
  APT0. No malformed-input-normalizer guarantee or actual GnuTLS acceptance.
  [Proof](evidence/B02-libunistring-install.json).
- NSS3.126-1+toddy1 OWNED/294payload; five bounded originals2271passes/three disabled
  cases unexecuted,745ELFs retained. Two test modules omitted only from verified
  production copy. Initial install0/post1 missing entropy device in bare chroot;
  verify-only2 recipe/post0/0,294payload/archive unchanged, ZERO root changes.
  Installed crypto/private SQL database/invalid DER refusal/unchanged listing/
  cleanup/SDK/APT0; private mount namespace exposes only four standard character
  devices, no disks/persistent mounts. [Proof](evidence/B02-nss-install.json).
- NSS partial patch reconciliation receipt`nss-input-reconcile-1.json` COMPLETE:
  all4845archive files reviewed; four patch changes retained, only manifest DIRS
  append completed. Derived patch changes only final hunk context, same five
  build/install changes; no runtime/fuzzy patch. NEVER repeat preparation, whole
  official/derived patch or reconciliation. ADR0162/config nss-patches.lock.json.
- libpsl0.23.3 OWNED/install/post0/0 changed21paths; eight original programs
  (five suffix/cookie/domain plus three finite corpus drivers, no fuzz campaign),
  32ELFs retained. Expected-five count reconciled metadata-only2; installed actual
  ICU UTF8/private runtime-list/wildcard/exception/cookie/converter refusal/recovery/
  SDK/APT0. [Proof](evidence/B02-libpsl-install.json). ICU78.3 backend reused.
- libical4.0.5 and NSPR4.40 OWNED. Calendar65CTest passes plus unchanged recur with
  identical private writable file; own borrowed-RRULE unref fixed consumer-only,
  verify-only0/0 and187payload/archive unchanged, zero root changes. NSPR three
  original runtime programs; own SDK4.40vs4.40.0 assertion reconciled verify-only,
  91payload/archive unchanged, sole generated APT cache change. ADR0161/evidence.
- Keyring50/libsecret/Gcr3/Gcr4/P11/libtasn1 OWNED. Production Keyring test hooks
  disabled;57original production programs plus five PRIVATE debug-only fixtures,
  332productionELFs unchanged. Actual isolated backend six store/read/lock/refusal/
  Stop/wrong-master/restart outcomes0; no real secrets retained. Native PAM/GNOME/
  permission UI remain pending. ADR0158–0160 and evidence index preserve failures.
- GNOME session/UPower/AccountsService/Systemd/PAM/Polkit/DConf/GJS/GTK/Mutter/Mesa/
  Libadwaita and earlier graphics/audio/input dependencies OWNED with bounded
  native evidence in [index](evidence/B02.md). This is NOT desktop/login/apps,
  audible routing, physical GPU/battery or native focus acceptance.

## Pending shared resources and runtime gates

GTK-owned gschemas.compiled needs controlled same-version union for GNOME session,
Gcr3/Keyring/future Shell schemas. Systemd-owned hwdb.bin needs controlled update
for two UPower rules, preserving full owned payload except declared cache/legal.
DConf GIO module cache is tracked generated resource; future glib-networking needs
controlled regeneration/affected GSettings/TLS checks. NSS currently keeps upstream
bundled roots; p11-kit/make-ca/unified-root switch is UNQUALIFIED. Do not overwrite
owned caches/providers ad hoc. EDS3.60.2/libsoup3.6.6 frozen/cached, unbuilt; EDS
requires libsoup unconditionally. Preserve owned nghttp2 1.71.0 security overlay.

Optional Polkit socket-helper profile is PARKED after two failed corrections;
standard SUID helper separately qualified/owned. Do not reopen unchanged socket
transport, reset its budget or advertise native permission UI acceptance.
Failure ledger `.local/phase2/failures.json` persists cause/input/attempt identity.
After two failed corrections or30minutes same-cause diagnosis, park that cause;
healthy progressing builds are monitored, not restarted. One guest writer only.

## Environment, recovery and publication

Builder boot568b17f7-1b0d-4b6c-bcd4-8fba4913a526. Target
`/mnt/lfs=/dev/vdb4/TODDY-LFS-TARGET`; builderroot`/dev/vda1/TODDY-BUILDER`.
Last measured targetfree20131340288B/hostfree112567934976B; remeasure before
allocations, preserve target16GiB/host100GiB reserves. Six existing scratch mounts:
gtk/desktop-resources/doxygen/glycin/pam/systemd-pam. NEVER recreate/reformat them.
After cold boot and verified prior-child cleanup/backing identity, inspect actual
mounts and use `virtual_discard_checkpoint.restore_volumes()` ONLY (print result),
not main/trim. Separately guarded `prepare_systemd_pam_input.py --restore` restores
same source bind: sourceinode8930333/inputinode7547189,7193files/SHA
2a683ffe0cdab7349a4b2b64b932fab647baaab4e7ab5b7c64520ff3443c5667.
All prior native children stopped; NEVER boot stale overlays after backing changed.

All earlier custodies/trims COMPLETE; NEVER replay retirement/discard. Inactive
Mozilla140.14 expanded source archive952148485B/SHA
0034632f70329e0bdf92f5d6fdd4cd9d08721f041f989abee65bfc5e5655dea6,
full actual422093entry restore verified before retirement. Current140.17source/
compiled/tests retained. [Custody/recovery](evidence/B02-runtime-custody-checkpoint.md).
Restore into a NEW absent private path only after full archive/manifest check.

Latest verified public495e4120043bd9f335b9f6874849c938cfa6a1a8: safety42692748744/
planning42692749158/Pages42692748869 allsuccess; exact public HTTP200/indexSHA
bad4f5bca19631af7948f1c0283967255d2cf1045664e81062360c8614948963 verified.
Historical GitHub internal zero-job failures/retry retained; no further unchanged
retry. Select checks by changed impact, no unchanged long suites. Commit/push
validated slices and verify exact committed public page. No host installation/
physical disk/global security weakening/paid services/new agents/model change/
workstation RAG. Finish ALL B02, then honor requested stop.
