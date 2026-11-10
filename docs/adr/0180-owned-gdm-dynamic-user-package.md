# ADR-0180: Owned GDM50 dynamic-user package

Status: native package/SDK/group initialization accepted; greeter/login pending.

Preserve the exact accepted GDM50.2 source/build/79ELFs/218stagefiles (ADR0178),
qualified Check SDK and actual shared PAM native gate (ADR0179). Native promotion
requires those same inputs and14unchanged installed PAM/module artifacts; never
rebuild accepted libraries or re-run their original suites for packaging.

The frozen BLFS13.1-systemd x/gdm.html page (SHA256
`5cc9af150aadbce31402194ce5d5f11d6e227eca21a51858ed05a3be0ccdee17`)
and actual daemon/gdm-dynamic-user-store.c/gdm-launch-environment.c require
modern userdb greeters and ONLY a dedicated group21. This corrects the earlier
handoff's anticipated static UID21 account. No such account was created. Actual
config enables HAVE_USERDB; installed libnss_systemd.so.2 and existing passwd/group
files+systemd NSS already support it. Do not downgrade to legacy users or rewrite
NSS/foundation packages. Persistent /var/lib/gdm is root:root0755, as upstream's
migration code explicitly enforces; per-greeter homes remain under /run/gdm/home.

Keep full local Wayland daemon/libgdm/GI/pam_gdm/PAM/Systemd/journal, upstream D-Bus/
Polkit/unit boundaries and existing GDM PAM includes. The supported X11 path is
omitted. The package owns all five GDM PAM files and custom.conf as conffiles.
Factory automatic/timed login stays false; InitialSetupEnable=false because the
native installer creates the owner and optional GNOME initial setup is absent.
No service activation, blanket udev-rule override, permissive PAM fallback or
additional helper privilege is applied. Unqualified fingerprint/smartcard providers
remain unavailable; upstream policy filenames do not qualify their hardware.

Add declarative group-only sysusers and root0755 state-directory tmpfiles metadata.
Initial package installation succeeded (588owned entries/archive), but its wrapper
then failed127 because this target has no optional systemd-sysusers executable.
Check actual group21/name absence and package/archive state before any correction.
Use frozen BLFS's existing Shadow groupadd rather than rebuilding Systemd for a
convenience tool. Separate group-init2 verifies all588payload entries/archive first,
creates ONLY the missing group and preserves passwd/shadow. Recipe/post0/0,
5changedpaths; no native package/source/compiler/original-test replay. Current
recipe uses the same initializer. Declarative metadata does not claim the absent
sysusers executable is available; the reproducible recipe performs groupadd.

Actual installed UID101 C libgdm client/extensions/copy/precancel/refusal/recovery,
GI1.0 client extension imports, SDK/CLI and package audits passed. No obsolete
static GDM user exists; group21/root0755 directory/defaults are verified and no
display-manager alias is enabled. This is package/ABI evidence, NOT a running
GDM greeter, PAM/keyring login, userdb lifecycle, graphical focus or physical test.
[Native package, original failure and group-only recovery](../evidence/B02-gdm-install.json).

Retain exact GPL2 source notices/leading headers and documentation legal.xml
notices. Documentation permits GFDL1.1 or later without invariant/cover text;
include the already qualified complete GFDL1.3 text from LICENSES/GFDL-1.3.txt,
with its exact hash in the inventory and copyright, without relabeling source.

Next selected SettingsDaemon50.1/Shell50.4 plus controlled GTK-owned NMA/GDM/plugin
schema union, then actual GDM dynamic identity/PAM/keyring/permission/Stop/recovery
and native GNOME/login/apps/offline/focus gates. No G2/B02 completion is inferred.
