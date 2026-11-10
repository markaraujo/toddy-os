# Phase 2 continuation card

Owner boundary: **complete ALL B02, then stop before another story**. B01/B03
accepted, B02 in_progress; B04 final integration blocked, B05–B13/G2 pending.
Weighted Phase2 accepted progress13%; no partial B02 percentage. ADR0113 records
owner authorization before B01. Physical foundation tests remain unperformed.
No complete native GNOME/login/basic apps or Phase2 ISO exists yet.

## Current slice and exact next action

Current slice: owned shared login PAM policy NATIVE GATE PASSED; no writer.
Install2/post0/0,15paths/14entries; four new conffiles, all prior policies/modules
unchanged, archiveSHAf67aea344d5ded8e5aa988bf9f15d3effbc813211cd708b15b2b1344921a8e59.
Fresh native kernel7.1.8/Systemd PID1 gate15expected outcomes and two actual
PAM/logind/user-bus cycles0; root PAM token change/old refusal/new recovery,
proper-argc unprivileged refusal64/no shadow change, locked/expired/missing/empty/
wrong refusal/recovery, PAMName Stop/MainPID0. Expired auth0/account13 is a REFUSAL,
never authorization. Stop before token is not in-flight PAM cancellation.
All14bound artifacts unchanged, synthetic user/wrappers removed, new bus per
cycle, explicit terminate-user cleanup. [Native proof](evidence/B02-login-policy-native.json),
ADR0179. Context `.local/phase2/native-login-policy-runtime-1` is COMPLETE; child
exited0/OOMfalse and backing unchanged before restart. NEVER rerun it or boot its
old overlay after parent restart. No GDM/greeter/GUI/hardware acceptance.
Builder restarted; six existing scratch FSs and same Systemd source bind restored;
owned policy14entries verified/ephemeral user absent in parent. Recovery receipt
`/var/log/toddy/phase2/login-policy-builder-restore-1.json` COMPLETE. Current boot
e540bdef-376f-46ae-9527-58d9641af256. No current guest/native writer.

Exact next: qualify accepted GDM50.2 source/CheckSDK/79ELFs/218stagefiles and
review its account/sysusers/directories/conffiles/policy package prerequisites;
create native GDM recipe/package, fixed lockedUID/GID21 only after absence checks.
Preserve GTK-owned schema cache; GDM/NMA XMLs need controlled union before actual
GUI. Do not rebuild GDM, policy, PAM/Systemd binaries or repeat accepted native
gate. Then SettingsDaemon50.1/Shell50.4 and actual graphical gates.

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

The previously missing four includes now have exact owned policies. GDM account/
name/UID21/GID21/varlib and native package remain absent; no GDM daemon enabled.
Next after native policy qualification: GDM account/sysusers/directories/conffiles,
actual keyring/PAM/greeter, SettingsDaemon50.1/Shell50.4 and native graphical gates.
Preserve source GDM staging and accepted PAM binaries; no full suite replay.

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

Builder boote540bdef-376f-46ae-9527-58d9641af256. Target
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

Latest verified public5651ad35f91f0ecbd47248de9003c8ede3762fe6: planning42738341653/
safety42738341401/Pages42738341472 allsuccess; actual exact HTTP200/indexSHA
585a6e8b2a13b4f160126c8b15817b815a2a4f98003939e1f47e2e12bbfac1c4.
`.local/phase2/5651ad3-public-verified.json`. GDM staging slice committed/pushed.
make check passed291tests; `.local/phase2/gdm-stage-final-check.log`; staged secret
scan clean. No further test run for this publication-only checkpoint update.
No host installation, physical disk/global security weakening/paid services/new
agents/model switching/workstation RAG. Finish ALL B02, then requested stop.
