# ADR0245: Fresh GNOME live owner and exact installer authority

Status: Accepted source contract; native qualification pending

Date: 2026-11-16

## Context

The Phase2 live image needs a fresh ordinary GNOME owner. H10's root-console
rescue profile is not the default GDM session. A locked-root passwordless live
session cannot use a generic auth_admin password to open the installer, and must
not acquire generic root, executor or installed-package authorization.

## Decision

After real generation2 archive finalization and independent image attribution,
apply the fixed source-attributed live profile: fresh locked toddy-live UID/GID1000,
empty private home, unchanged locked root/empty wheel97, frozen GDM50.2 Wayland
autologin with a narrow live/user PAM guard, and scoped ephemeral lock/idle defaults.
Never copy a builder/live home into an installed target. Frozen GDM50.2,
Linux-PAM1.7.2, Polkit127 and GSettings50.1 primary sources define the exact
configuration/PAM/program-detail/schema contracts; native runtime proof is still
required. Keep original foundation recovery artifacts unchanged.

The live-only Polkit rule matches only the fixed Install action and root entry,
local active subject toddy-live. The actual root entry independently checks UID1000,
protected ID=toddy/imageclass/source/unit, actual toddy.live kernel flag, original
H10 media-ID marker, current boot, running root producer PID/cgroup/invocation and
actual active unlocked local GDM Wayland session. A0700 root systemd runtime
producer publishes a0644 attestation bound to these facts. The root guard rechecks
current facts rather than trusting marker/caller data; logout/restart/another boot
cannot inherit authority. No installed acquisition/executor policy is weakened.

Media identity derives from payload manifest/policy/live profile source before
compression; image/rootfs hashes are measured independently to avoid circular
self-hashes. Preserve exact pre/post live delta, native Dconf output, H10 ACL
sidecar and complete compression snapshot/journal. Never reinterpret candidate
metadata or passed booleans as native finalizer/boot authorization.

## Consequences and validation

No global X11/Wayland permission weakening, owner environment/keyring inheritance,
provider request, model, root grant or arbitrary hook/command is introduced.
The installed offline projection must exclude live user/profile/rule/unit/class/
helper/runtime markers and use its own fresh owner/identity path. Existing
reviewed disk plan, confirmation, password FD, Stop and signed composition gates
remain mandatory. GDM's once-per-boot autologin may require a live reboot after a
deliberate logout; there is no password/root-console fallback. Qualify actual
usability before release. Source tests cover mismatch/refusal/attribution only.
Actual live GDM/PAM/Polkit/rootGUI/session lifetime and installed exclusion tests
remain pending, as detailed in [the operator contract](../native-live-session.md).
