# ADR-0186: Real native Shell capture and late automation hook

Status: native Shell overview captured; second interaction gate failed, correction pending.

Native2 committedinput42736b773815d0672c9f27a31462939d6315687f preverified4412files
across owned Shell/Mutter/GTK/Gst/Base. New disposable no-NIC overlay, real kernel
7.1.8/Systemd, synthetic locked-account user12401, accepted PAM session-consumer
binary (no credential-suite replay/password/owner credentials). Actual PAM/logind
session/user manager/user bus registered and closed0/0; runtime/account removed.
This is not GDM or authenticated graphical login.

Actual Shell renderer/panel/overview are visible in the unedited native1280×720
[diagnostic PNG](../evidence/screenshots/B02-shell2-overview-diagnostic.png), SHA256
`ce5e4ccfd0664514513ee84ee3decd740900b097165ea94e9cd1f0c8ae372407`.
Visual inspection confirms top panel/time/search/overview/workspace geometry;
required basic applications are absent, so no app/interaction/focus acceptance.
The first native Gst/NoSuchUser exceptions are resolved by the new dependencies/
session; actual Settings/IBus portal/audio/camera/colord integration remains pending.
Native2 action runner never began within150s: actionsnull/zero, one diagnostic
PNG only. Timeout remains failure. State records startingUpfalse, one monitor,
panel1280×32/stage1280×720. Exact logs/result retained.
[Actual failed gate, registered session, image and recovery](../evidence/B02-shell-second-native-failed.json).

Source evidence narrows the next hypothesis: main.js starts LayoutManager during
_initializeUI, then awaits importing Scripting/the automation module before attaching
its startup-complete handler. layout.js sets _startingUpfalse immediately before
emitting startup-complete. The native diagnostic sees startup complete but no
GNOME-start/automation callback; no intervening JS exception is logged. A missed
startup signal is a source-backed hypothesis, not yet a proven corrected result.

Correct ONLY the automation fixture's supported init hook: if _startingUp is already
false at init, schedule the same upstream Scripting.runPerfScript once from idle.
If startup is pending, retain upstream's ordinary handler. Do not patch the Shell,
force its state, emit a fake startup signal or enable unsafe-mode. Keep initial/
5s/45s observational state history rather than overwriting the initial observation.
Use the existing bounded/checksummed compressed SMBIOS transport as the expanded
probe exceeds the direct payload budget; decoded raw source hash remains verified.
Fresh native3 only after committed inputs/preflight. Persistent cause ledger records
second corrective attempt; preserve native1/native2, no unchanged replay.

Actual native2 child exited0/OOMfalse/backing unchanged before builder restart.
Restored only the same six scratch filesystems and7193-file authenticated Systemd
source bind. Receipt shell-builder-restore-2 complete; new builderboot
bc427e89-6fc4-40c5-8113-6581e54c8111. Never repeat restore2 or boot old overlays.
Targetfree17386262528B, close to16GiB reserve; future large application work needs
new verified custody/allocation review, not deletion of accepted evidence.

After two failed corrections/30min same-cause diagnosis, park the blocked native
interaction cause and move to required basic-app work; retain precise new unblock
conditions. Healthy progressing builds are not diagnosis. All B02 criteria remain
open until actual login/basic apps/offline/service/resource gates pass.
