# ADR-0060: Verify static DBus activation and preserve offline network startup

- Date: 2026-11-06
- Status: Native offline policy verified in private roots; H08/boot execution pending

Private integration work found two defects in the prepared H08 service policy.
The original postcheck expected dbus.socket to report enabled. The actual frozen
DBus 1.16.2 unit has no [Install] section and native Systemd reports static.
Its package-owned usr/lib/systemd/system/sockets.target.wants/dbus.socket link
already activates it through sockets.target. Treating static as a failure would
stop H08 despite the correct vendor activation. Do not add a redundant generated
link or change the upstream unit merely to satisfy the old expectation.

The second failure appeared when the real native systemctl preset-all was run
against copied source-owned units and the prepared higher-priority Toddy preset.
Despite disable systemd-networkd-wait-online.service, networkd's Also= installed
its wait-online link again. Native state changed from disabled to enabled.
The frozen vendor preset also requests that service; the Toddy rule alone does
not prevent its indirect activation through networkd's installation metadata.

## Decision and book deviation

Use a shared offline_services.py component for H08 configuration and checks,
reusable by fresh image assembly. Verify all 329 installed Systemd/DBus unit
paths against their own package records before invoking native Systemctl.
Require DBus's exact root-owned vendor socket link and static state. Enable
networkd, resolved and timesyncd, select multi-user.target, disable wait-online,
then mask only systemd-networkd-wait-online.service to /dev/null. All Systemctl
commands use an explicit --root and do not contact a running service manager.
The production CLI still requires completed H07, H08 in_progress and real native
metadata closure. No running build inputs or target configuration changed here.

LFS 13.1-systemd section 9.2 discusses disabling networkd-wait-online when
networkd is not used. Toddy does use networkd: disabling its wait helper is an
explicit offline-boot policy deviation, not a verbatim book instruction. The
mask preserves that chosen policy against the reproduced preset behavior. Networkd,
DNS and time synchronization remain enabled; no network security control is
disabled. The mask applies only to the designated Toddy target/image, never the
workstation or builder OS. An owner who deliberately wants network-online waiting
can unmask and enable this service on Toddy; this bootstrap helper is not an
ongoing reconciler that overrides later owner choices.

The unowned-file audit recognizes only this exact root-owned /dev/null link,
backed by the real regular Systemd-owned wait-online unit under physical parents.
Other masks, other link targets, non-root ownership, absent ownership or a
redirected backing unit are not accepted as this generated policy. Ordinary
enablement links still must resolve inside the selected image to native owned
units. No arbitrary /dev/null-link exception is added.

Alternatives: leaving disable alone loses the policy after presets; treating
enabled wait-online as acceptable changes the selected offline behavior; a full
networkd unit override would duplicate unrelated upstream service/security
settings and need maintenance on every update. The actual config_parse_also
implementation appends names and does not clear the list for an empty Also=,
so an empty drop-in assignment is not a supported removal mechanism here.
One reversible mask preserves the upstream unit and other installation links.

## Native evidence and remaining limits

python3 scripts/host/probe_offline_services.py copies the actual own unit files
and vendor preset into a disposable root. It reproduces the old static/enabled
mismatch, executes the new shared component, repeats configuration and checks
stable links, runs read-only verification, then reapplies native preset-all and
checks the policy again. All three services stay enabled, DBus stays static,
wait-online stays masked and multi-user.target stays selected. There are 15
generated links after explicit configuration and 39 after the full vendor/Toddy
preset application; every non-mask link resolves to a verified owned unit.
The extra preset links exist only in the private probe, not the installed target.

Six negative cases preserve their inputs and are refused: missing/changed DBus
vendor link, altered native unit bytes, unowned generated link, disabled required
service and redirected configuration directory. The unowned-link case also
omits a required enablement link and calls the mutating entry: preflight refuses
before repairing anything, proving preservation before configuration. Five audit boundaries reject
missing ownership, another masked service, another mask target, non-root mask
ownership and redirected source unit. Installed Systemd configuration and Dpkg
status remain unchanged. Successful private fixtures are removed after retaining
complete operations/results. No service is started by this experiment.

Original failed preset report SHA-256:
80fbef6306b5002523bf1c5f7b1c50c659d1c3764c174493cf4798eb5f3f7468.
Preserved fixture: /mnt/lfs/tmp/toddy-offline-services-8nmlgzef, including
native-preset-all.log. Final report .local/logs/h08-offline-services-probe.json
SHA-256 302bb71d433ea76ad1c9e4a5ac613e8420754bed4251de300383d73cced88c18.
Tested helper SHA-256:
c6fd34504c02ad4204f4752348b5ea2a85a82e242e87cf8bf1e2025507871aeb.
Auditor SHA-256:
8d8231d71989b1bc451139551ecb7b12999ddd8b596165661f871882811c95c7.
Toddy preset SHA-256:
ad9371e673bf43d6b7c9b7b66793eb8be36e71feb598b92089dc4ae2539036bf.
Native vendor preset SHA-256:
ad4f37d36408ed061a1631c47414fa428bc82ede4f878924c7e0bbad7cee4fbf.

Primary sources inspected directly: frozen LFS 13.1-systemd chapter09/network.html
(SHA-256 f1b27e4b689a7a47f6a777b8d5307dd0a613df3a2d2e48061e4b88ee2b8e524e),
native DBus 1.16.2 units/vendor link, Systemd 261.2 units/presets,
src/shared/install.c and src/core/manager.c. Systemd source archive SHA-256:
ed1059ff964f5df35b6056434cc17cc83f86dc913f10489948a0b19b6081c5ec.
Systemd can apply presets on first boot, subject to its first-boot detection;
this probe explicitly invokes preset-all and does not claim that an empty live
machine-id automatically triggers it. The native report pins both provider
package archive identities and verifies their installed unit bytes.

This amends ADR-0042's enablement wording and wait-online handling. H08 package
installation, actual service activation, DHCP/DNS/time synchronization, offline
boot timing and BIOS/UEFI/USB behavior remain required target acceptance work.
Private offline configuration is not a network or boot pass; G1 remains pending.
