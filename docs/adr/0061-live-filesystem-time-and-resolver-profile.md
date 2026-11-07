# ADR-0061: Generate a fresh live filesystem, timezone and resolver profile

- Date: 2026-11-07
- Status: Native private-root checks passed; final image integration pending

The prepared H08 base configuration describes the installed build disk. A live
image must not activate that disk's root/swap entries or inherit the builder's
resolver data. Its verified media, compressed root and writable overlay are
mounted by the explicit initramfs path, before Systemd starts.

Use h10/live_configuration.py only in a fresh private image stage. Replace the
exact original base-package fstab with a comments-only live profile; generate
localtime pointing to the source-owned UTC data and resolv.conf pointing to
/run/systemd/resolve/stub-resolv.conf. Require empty physical runtime directories,
same-filesystem configuration/timezone inputs, root-owned regular fstab with one
link, exact source hashes and absent generated defaults. Refuse altered inputs,
redirected parents and interrupted partial output before configuration changes.

The final assembler must obtain the original fstab hash from the accepted base
package and record this explicit conffile transformation in its final audit.
Keep native package metadata unchanged: replacing archive/database hashes to
hide a configured conffile would misrepresent package provenance. The helper
does not provide a production command that bypasses the H08/H10 gates.

Alternatives: copying the build fstab would retain inappropriate disk mounts;
copying resolver bytes would freeze builder-specific network state; deleting
package conffile metadata would destroy the recorded ownership relationship.
Fresh generated configuration preserves both live semantics and provenance.

Primary sources inspected: the frozen LFS 13.1-systemd base configuration
represented by h08/stage_config.py; Systemd 261.2 src/shared/fstab-util.c,
src/fstab-generator/fstab-generator.c, src/basic/proc-cmdline.c and
src/basic/initrd-util.c. Systemd source archive SHA-256:
ed1059ff964f5df35b6056434cc17cc83f86dc913f10489948a0b19b6081c5ec.
Native non-initrd fstab generation legitimately enables the remount service
even when fstab contains no mounts; that link is not an inherited disk mount.

## Evidence and limits

python3 scripts/host/probe_live_configuration.py generated the current base
configuration candidate in a private root, then used actual source-owned native
Findmnt, Coreutils Date, Glibc and Systemd generator programs/libraries.
Findmnt returned success without warnings; Date returned +0000; the generator
returned zero and created only the expected systemd-remount-fs.service wants
link, with no generated mount/swap units. Eleven refusal cases preserved fstab
and default-link state: changed fstab, existing resolver, existing timezone link,
redirected etc, inherited runtime data, redirected run, changed UTC, interrupted
partial output, wrong base hash, unreviewed link policy and hardlinked fstab.
Installed configuration and Dpkg status remained unchanged.

Report: .local/logs/h10-live-configuration-probe.json, SHA-256
87272eae938e2f942ae88fe8f688996300bd5c37e38986a9f367fec1db52acab.
Tested helper SHA-256:
dd48e2bf6105510d7870fb2ce5086340c60839372671fe90dd3c7ae6efd424c2.
Original candidate fstab SHA-256:
0f3c228b5388f3c4de3e4322186157061e51c4fb27598803a5f283300ef9e47c.
Live fstab SHA-256:
65b0311609ea5c205d2dadb82e759b269cd40766f43169f454e9231609fdfddc.

The base candidate was not packaged or installed. Actual H08 installation,
accepted-package integration, boot mounts, DHCP/DNS, live overlay and installer
generation of a separate disk profile remain required. No native Toddy boot or
DNS success is claimed. Preserve any interrupted private stage for diagnosis,
then reconstruct from accepted inputs; do not replay this transformation over
unknown output or installed-system configuration.
