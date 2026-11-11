# ADR-0226: Explicit desktop NetworkManager ownership with networkd recovery

Status: accepted recipe; native installation and runtime qualification pending
Date: 2026-11-11
Scope: B02 desktop network integration in the designated guest only

Actual target inspection found NetworkManager1.58.1 installed and disabled,
systemd-networkd enabled with the owned foundation IPv4 DHCP configuration, and
systemd-resolved enabled. The native Settings Network page previously reported
the inactive NetworkManager. Starting a second DHCP manager on the interface
would leave ambiguous network ownership.

Stage a small original `toddy-desktop-network` configuration package. A root-owned
conffile marker `/etc/toddy/network/use-networkmanager` selects NetworkManager.
Its service gets a positive ConditionPathExists drop-in; networkd gets the inverse
condition. Keep the existing foundation networkd wants link and DHCP file for
recovery. Add only NetworkManager's multi-user wants link. Do not enable its
optional wait-online service: offline desktop boot has no network prerequisite.
Keep stock dispatcher activation and all upstream service security settings.

Use keyfile profiles and the existing systemd-resolved DNS integration. Preserve
the resolver symlink, owner connection profiles, credentials, hostname and higher
priority configuration. The package supplies no credential or connection profile.
Networking-off in NetworkManager does not select networkd; the owner marker
continues to select the disabled-network state until an administrator changes it.

All four regular files under /etc are conffiles. An initial install refuses
existing files at its exact owned destinations. The native transaction backend
and full verification required for an unqualified recipe remain mandatory; no
daemon is started in the builder chroot. The install/postcheck recipes are
prepared while the Firefox compiler owns the guest and must not run concurrently.

Recovery explicitly stops the current manager before moving/restoring the marker
and starting the other manager or rebooting. Check actual interface/address/route/
DNS state. The original DHCP configuration remains available. Uninstalling or
manually overriding this policy needs the same explicit manager transition.

Host fixture tests run the real systemd condition evaluator against temporary
staged paths for marker presence/absence, proving inverse conditions, daemon-only
enablement and stage preservation. They do not prove target Systemd261/PID1,
NetworkManager startup, normal-user polkit, DHCP/DNS, GUI navigation/offline states,
reboot persistence or recovery. Those native checks are required before B02
acceptance. Physical networking/Wi-Fi hardware remains unverified.

Inputs: installed owned NetworkManager1.58.1-1+toddy1 stock service unit,
Systemd261.2-1+toddy3 networkd/resolved units and toddy-base-config0.1-1 DHCP file;
read-only target inspection2026-11-11. [Prepared recipe evidence](../evidence/B02-desktop-network-prepared.json).
