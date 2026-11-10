# ADR-0176: Owned NetworkManager daemon and scoped native SDK

Status: package/SDK accepted; actual daemon/network/permission/desktop gates pending.

Build pinned NetworkManager1.58.1 from the official source SHA256
`262864cfd198123d3e5dbe91937441b97ee9059d6d712e1a5bfbb1c54668d14d`,
selected by frozen BLFS13.1-systemd basicnet/networkmanager.html. Actual Meson
requires libndp; reuse ADR0175's owned1.9, existing GLib/Systemd/DBus/Polkit,
GnuTLS/default trust, PSL/Curl/Readline and UUID dependencies. No frozen foundation
version is replaced. Source configuration is the contract, rather than importing
an obsolete distro-specific networking recipe.

Keep the full daemon, libnm, nmcli, GI1.0/Vala, WiFi support, internal DHCP client,
Systemd/logind/session tracking/journal, Polkit authorization, GnuTLS and public
suffix/connectivity support. Do not set no-auth groups or disable Polkit. Optional
cellular/PPP, Open vSwitch/cloud automation, nmtui/Qt examples, alternate distro
configuration plugins, CLAT/eBPF/NBFT are omitted through supported options.
SELinux/audit-library support is not installed by this profile; existing global
security is unchanged. WiFi compilation does not prove hardware/supplicant paths.
Factory network activation/DNS ownership must be integrated separately: installing
this package does not enable the daemon or hand it the builder/host network.

The unprivileged read-only-input/no-route build compiled613ELFs and staged285regular
files. All67registered original test programs returned0/OK. Preserve20nested TAP
skips, including absent compiler-namespace CA directory and optional JSON/team
validation; none is a pass. Original keyfile/settings/secrets/crypto, supplicant,
DHCP helpers, client/secret-agent mocks, dispatch environment and unit checks are
bounded source/fixture evidence, not actual daemon authorization or wire traffic.
Original platform tests do not substitute for real guest device/network testing.
Own C consumer roundtrips a typed UTF8 static connection through actual libnm D-Bus
variants, refuses an invalid address and recovers twice; no daemon/network call.

Review privilege/network exposure explicitly: preserve installed D-Bus ownership
policy, Polkit actions, root service/helper boundaries and upstream units; no SUID
or SGID artifact exists in the staged payload. Actual methods must still pass real
unprivileged refusal/authorization, Stop/replay/recovery and connection persistence
checks before network/desktop acceptance. External DHCP/DNS/certificate/network
content remains untrusted data, never an administration permission source.
Pin native dependency versions and verify actual installed library resolution;
no remote provider/HTTPS/WiFi/hardware claim comes from this API consumer.

Native install recipe0/post1 changed672paths and owns831entries. The failed own
postcheck expected upstream version in CLI output, but the exact source option
`dist_version=ToddyOS` intentionally changes daemon/nmcli distribution labels.
Record upstream package/SDK1.58.1 separately from actual CLI distribution output
(ToddyOS / nmcli tool, version ToddyOS). Correct the check only; do not rebuild or
reinstall to fix an assertion that disagrees with the chosen source option.
Verify-only2 recipe/post0/0 and ZERO root changes preserved all831owned entries
and the archive. Installed UID101 C consumer/GI1.0/SDK/CLI/package audits passed.

Retain exact COPYING/COPYING.LGPL and bundled legal notices plus leading source
C/header notices, including GPL2-only/syscall exception, LGPL2+/2.1+, MIT and CC0
conditions. Per-file terms prevail; LGPL2-or-later portions can use the included
LGPL2.1 terms. No GPL-only module is relabeled LGPL. CLI distribution labels are
not upstream source identity; package/source/inventory remain explicitly1.58.1.

Next: actual native service policy/network/Stop/persistence gates and selected
NMA/GDM/GNOME Shell integration. No graphical desktop or B02 criterion is complete
by this package alone. [Source, original skips, install failure and verify-only proof](../evidence/B02-networkmanager-install.json).
