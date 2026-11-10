# Phase 2 continuation card

Owner boundary: **complete ALL B02, then stop before another story**. B01/B03
accepted, B02 in_progress; B04 final integration blocked, B05–B13/G2 pending.
Weighted Phase2 accepted progress13%; no partial B02 percentage. ADR0113 records
owner authorization before B01. Physical foundation tests remain unperformed.
No complete native GNOME/login/basic apps or Phase2 ISO exists yet.

## Current slice and exact next action

GDM50.2 build/original/stage passed; NO active guest writer. `gdm-1` controller
PID523211 terminal0,79compiled ELFs/218staged regular files. Actual original
m-common0, qualified private Check0.15.2 SDK/nine cases reused unchanged. Own
libgdm client extension-copy/precancel refusal/two-cycle recovery/CLI GDM50.2 passed.
Input `/mnt/lfs/sources/phase2/inputs/gdm-50.2`, work
`/mnt/lfs/sources/phase2/work/gdm-1`; authoritative job/log/exit
`/var/log/toddy/phase2/gdm-1.{job.json,log,exit}`.
SourceSHA8a4679e47cddfe8b0a1bd9d3836042deb68fb3e1b0e7e62dfd0631dc5b6fc541.
[Proof](evidence/B02-gdm-build.json), ADR0178/rawSHA
30946690e3467cfa4334ac1306bd7d799d6b10b7e6790645a6f32a7e285e3e77.
NEVER replay accepted build/original/Check SDK/stage/client checks.

**Concrete next prerequisite:** staged GDM LFS PAM policies include system-auth,
system-account, system-password, system-session; actual target has NONE. Required
PAM modules including unix/systemd/keyring exist. Other is deny-only; Polkit-auth
and systemd-user have their own policies. GDM account/name/UID21/GID21/varlib and
native package absent; no GDM daemon enabled/started. Native policy snapshot:
`.local/phase2/gdm-native-prereqs-1.json`; read-only inspector
`python3 .local/phase2/inspect-gdm-native-prereqs.py`.

Exact next: implement/qualify small owned Toddy login-policy package for the four
missing includes using frozen BLFS13.1 PAM policy and required logind session
integration (ADR0178). Preserve existing other/Polkit/systemd-user bytes, no nullok
or blanket permit. Reuse owned PAM1.7.2/Systemd261.2/Keyring50; no baseline rebuild.
Bind policies/module identities and actual native synthetic credential positive/
wrong/locked/expired/missing-user/session/Stop/recovery outcomes before GDM login
acceptance. Then reviewed GDM account/sysusers/directories/conffiles/native package,
SettingsDaemon50.1/Shell50.4. Do not replay uncertain state-changing operations.

## Accepted boundaries — reuse unchanged evidence

- libnma1.10.6 native install2/post0/0,174paths/346owned entries. Original test-utils0,
 101ELFs unchanged/114stagefiles; actual UID101 GTK3/4 C and selected NMA/NMA4 GI/
 Gcr4/Gck2/refusal/recovery/SDK0. Initial own registry/prewrite resume-map failures
 preserved. Sixteen manual GUIs compile only; nma-ws scanner warnings/full GI
 coverage and actual widgets/credentials/network unqualified. Two nm-applet schema
 XMLs need controlled stock cache union. ArchiveSHA
 2d70832c46983368c371475477a216d118144fc2c797daca560189eccdc05adb.
 ADR0177/[proof](evidence/B02-libnma-install.json).
- NetworkManager1.58.1 package owned:67original drivers/20nested skips,613ELFs.
 Install0/post own CLI-label1 reconciled verify-only2 0/0/rootchanges0,831entries
 unchanged. Actual UID101 C/GI/SDK0; upstream1.58.1 vs chosen CLI dist_versionToddyOS
 explicit. NO daemon/network/policy/persist/Stop/replay acceptance. ADR0176/
 [proof](evidence/B02-networkmanager-install.json). Never reinstall for a postcheck.
- libndp1.9 owned0/0,18paths/22entries; no upstream suite, actual typed five-message
 API/refusal/clamp/recovery0, no packets. ADR0175/[proof](evidence/B02-libndp-install.json).
- GeoClue2.8.2 full backend/lockedUID30 owned; verify-only2 0/0/root0. Native
 services3 actual config deny/peer isolation/global agent revoke+restore/Stop/two
 buses0/root0. Synthetic static source/agent; native non-sandboxed peer uses
 upstream system-app branch, no per-app auth/GNOME consent/provider/owner position
 proof. Failed private profiles1/2 retained, no live services. ADR0174/
 [proof](evidence/B02-geoclue-install.json).
- GTK4same-upstream4.22.4toddy7 stock82schemas/623keys preserves prior81/618 and
906nonlegal entries. Weather data2026.2/GWeather4.6.0/Geocode3.26.4 native evidence
 accepted; external METAR original DNS/SIGABRT remains unqualified, not a pass.
 GTK3same-upstream3.24.52toddy2 actual12IMmodules/11prior preserved. IBus installed
 default Composeã/cancel/refusal/recovery/Stop/two buses0; failed profiles1/2/3
 retained/no live processes. NEVER replay completed cache/install transactions.
- Earlier GNOME-session/UPower/Accounts/Polkit/Systemd-PAM/PAM/Keyring/EDS/GJS/GTK/
 Mutter/Mesa/audio/input/crypto/trust/SDK evidence is indexed in
 [B02](evidence/B02.md). Actual library/headless evidence is NOT desktop/physical
 acceptance. No unchanged compiler/original-suite replay.

## Remaining real gates

Actual NM service/network/permission/persistence/Stop/replay/reconnect, GDM/PAM/
keyring/login, SettingsDaemon/Shell/native GTK keyboard/focus/accessibility, basic
browser/files/terminal/editor/settings/audio, navy defaults/offline/no agent,
resource measurements/security/ABI review and final B02 acceptance remain pending.
Stock GTK-owned schema union must include NMA/GDM/upcoming owned schemas without
changing prior key contracts/preferences. Systemd-owned hwdb update for two UPower
rules, p11 local trust callback/update/recovery/NSS unified-root alias and default
Glycin/fresh combined qualification remain required where affected.

Optional Polkit socket-helper branch PARKED after two failed corrections; standard
SUID helper separately qualified/owned. Never reopen unchanged socket transport.
Persistent failure ledger `.local/phase2/failures.json` preserves cause/input/budget
across compaction. After two failed corrections or30minutes same-cause diagnosis,
park that cause and select eligible work. Healthy progressing builds are monitored.

## Environment, recovery and publication

Builder boot568b17f7-1b0d-4b6c-bcd4-8fba4913a526. Target
`/mnt/lfs=/dev/vdb4/TODDY-LFS-TARGET`; builderroot`/dev/vda1/TODDY-BUILDER`.
Last targetfree17961508864B before small GDM input; measure target/host before
allocation, preserve target16GiB/host100GiB reserves. Six existing scratch volumes:
gtk/desktop-resources/doxygen/glycin/pam/systemd-pam. NEVER recreate/format them.
After cold boot verify child cleanup/backing identities, then only
`virtual_discard_checkpoint.restore_volumes()` (not main/trim); separately guarded
`prepare_systemd_pam_input.py --restore`. Sourcebind inode8930333/input7547189,
7193files/SHA2a683ffe0cdab7349a4b2b64b932fab647baaab4e7ab5b7c64520ff3443c5667.
No previous native child is live; NEVER boot a stale overlay after backing changes.

Earlier custody/trims COMPLETE: never replay retirement/discard. Inactive
Mozilla140.14 expanded source actual422093entry restore was verified before
retirement; current140.17source/build/tests retained. Full archive/manifests and
recovery are in [custody index](evidence/B02-runtime-custody-checkpoint.md). Future
Firefox may require NEW qualified custody of inactive compiled work, not done.

Latest verified public c686143fc81ee30f805da54e56fd18ee37de7789: planning42737062132/
safety42737062085/Pages42737061869 allsuccess; actual exact HTTP200/indexSHA
159c06948f38637efc18f6bfc0583e94a708291cb1c85bfa58799e8046a5905d.
`.local/phase2/c686143-public-verified.json`. GDM staging slice publication next.
Previous checks291passed; run make check for changed source-preparation/SDK branch
and repository delivery only, no unchanged long suites. No host installation,
physical disk/global security weakening/paid services/new agents/model switching/
workstation RAG. Finish ALL B02, then honor requested stop.
