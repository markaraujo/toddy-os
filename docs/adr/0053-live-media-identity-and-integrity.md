# ADR-0053: Bind live-root verification to generated initramfs metadata

- Date: 2026-11-06
- Status: Native integrity component verified; media discovery and boot integration pending

Frozen BLFS 13.1 postlfs/initramfs.html supplies the early-userspace/root-mount
sequence. Toddy's compressed live root additionally needs a verified media
identity and root image before overlay setup. The kernel drivers and source
format choices remain those of ADR-0046/0047; this does not introduce another
distribution, initramfs framework or archive tool.

Use a fixed .toddy-media-id marker at the media root and live/rootfs.squashfs
for the compressed root. The generated initramfs must contain its expected
64-character lowercase hexadecimal media identity and root SHA-256. Discovery
may locate candidates by label, but a label alone never accepts a root. The
caller must mount each candidate read-only and verify these embedded values
before mounting its root image. The assembly step still has to generate the
matching data and establish the actual compressed filesystem format.

The prepared scripts/build/h10/live_media.sh component takes the candidate
mount path and both expected values. It validates argument count and digest
syntax, refuses redirected/missing media marker, payload directory and image,
compares identity, and hashes the image through standard input. Media text is
never sourced or evaluated as shell commands. Required tools are the already
verified minimal Bash/Cat/SHA256sum runtime; no new package is needed.

Native tests exercised ten cases with real private files and actual native
Bash/Coreutils: matching data, altered image bytes, wrong identity, malformed
embedded digest, command-like marker text, absent image, redirected image,
redirected payload directory, redirected media root, and restored valid data.
Failures returned 1 with diagnostics; valid cases returned 0. The injection
sentinel was absent and unrelated fixture bytes unchanged. Fixtures were
removed after checks; no installed files or active BDB inputs were modified.
The files deliberately contain harmless opaque data, not a synthetic claim
of a Squashfs or ISO image. This proves the integrity component only.

Reproduce with python3 scripts/host/probe_live_media.py. Raw evidence is
.local/logs/h10-native-media-integrity-probe.json, SHA-256
`ddcb764e41952d734cee4ecd4fd79122913be373fe4b30fdfc0f91b0dca9c48b`.
Tested component SHA-256:
`93cbae9d494dd54d10c9aa5681ad9a1c9a51467df4f57b87a43c1fa60fd5552e`.

Alternatives: accepting only an ISO label cannot distinguish stale/copied
metadata; trusting a digest supplied by that same candidate does not bind it
to the selected initramfs; evaluating configuration from the medium would turn
discovery data into code. Embedded expected data plus content verification
provides the intended pairing/corruption check. It is not publisher-signature
verification or a Secure Boot claim.

Actual device discovery, bounded waiting, recovery console, real media/format
checks, indexed overlay, ACL restoration, Systemd transition and BIOS/UEFI/USB
boot remain pending. The H09/H10 gates are unchanged. No script here installs
or boots a live image, and no milestone credit is assigned to preparation.
