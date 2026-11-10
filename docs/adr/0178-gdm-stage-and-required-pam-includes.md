# ADR-0178: GDM staging and the missing login PAM prerequisites

Status: original build/stage accepted; native policy/account/login work pending.

Build frozen GDM50.2 with local Wayland login, libgdm/GI, full PAM/pam_gdm,
Systemd/logind and journal. Disable only the supported X11 path and optional
SELinux/audit-library/Plymouth integrations. Reuse qualified private Check0.15.2
SDK from libfyaml, preserving its nine original cases and exact SDK hashes; no
new test-tool build or runtime installation. Build input records this custody.

Actual compile/original m-common/stage exit0,79compiled ELFs/218regular stagefiles.
Own actual libgdm client uses the two supported PAM extension IDs, verifies owned
extension copies, refuses a precancelled connection and recovers twice. Daemon
CLI is GDM50.2. This proves neither a greeter nor authentication or GI runtime.
Upstream gnome.post_install skipped its schema-cache command because DESTDIR was
set; current installed GTK-owned cache was not touched. Preserve that separation.
[Source/SDK/original/client/stage evidence](../evidence/B02-gdm-build.json).

Actual native preflight found no GDM package/account/name/UID21/GID21/varlib, but
all required existing PAM modules are owned, including pam_unix, pam_systemd and
pam_gnome_keyring. The staged LFS GDM policies include system-auth, system-account,
system-password and system-session. NONE of those files exists in the target.
Do not install these policies and advertise functional login while their includes
are missing. Native promotion/acceptance needs explicit owned login policy first.

The frozen BLFS13.1-systemd postlfs/linux-pam.html section documents the four generic
policies (book page SHA256
`341f6f23114e22d4a8a1f23b7664be1ecb9d6f53909afe1f1a22ed19e7fc4c26`).
Its auth/account/session use pam_unix; password uses yescrypt/shadow/try_first_pass.
Do not adopt its permissive illustrative other/nullok example. The actual target
other policy remains deny-only, and actual Polkit/systemd-user policies are separate.
Systemd-user already has pam_loginuid/pam_namespace/pam_systemd and requires no
unrelated baseline rebuild or blanket relaxation for this missing-prerequisite fix.

Next implement and qualify a small owned Toddy login-policy package for these
missing includes, with no nullok/auth permit bypass and with the GDM session's
required logind integration. Preserve other/Polkit/systemd-user bytes. Bind exact
policy files/modules, test actual positive authentication plus wrong password,
locked/expired/missing-account refusal, session/Stop/recovery, then integrate GDM
account/sysusers/directories/conffiles. Test privileged behavior in the designated
native guest using synthetic credentials; never ask for or log an owner's password.
No accepted PAM binaries/long original suites are rebuilt/repeated for policy data.

GDM account/greeter/PAM/keyring/permission/replay/recovery, stock schema union and
actual native graphical login remain required. Keep fingerprint/smartcard paths
unavailable until their providers qualify; installing upstream policy files does
not make missing hardware/modules available. Continue SettingsDaemon/Shell and
basic apps after prerequisites, without a general architectural replan.
