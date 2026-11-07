# H13 public GitHub foundation prerelease

Published 2026-11-07 as
[`v0.1.0-foundation.1`](https://github.com/markaraujo/toddy-os/releases/tag/v0.1.0-foundation.1).
This is the accepted G1 command-line VM foundation, not the G2 desktop, agent or
installer release. The actual ISO was built and tested from commit
`e24e452399621607a8386db582e5776bd66994da`. The public tag points to
`b474b1088ee4c98d64ab3985b731203cf94fc1ac`, which adds the owner's approved
MIT and CC BY 4.0 grants without changing the ISO bytes. B01-B13 remain
not_started pending separate owner approval.

The ten public assets are the ISO, corresponding source tar, component/source
inventories, source checksums, complete source-history bundle, scoped MIT and
CC BY 4.0 license files, licensing explanation and release-specific SHA256SUMS.
[Exact GitHub asset IDs, sizes and SHA-256 values](H13-github-release.json) match
the local candidate. All assets were downloaded through the draft release and
rehashed before publication. After publication the public checksum file was
downloaded without authentication and matched. The public ISO download route
responded HTTP 200 with the exact 1,095,000,064-byte size. The public Git tag
matches the licensed source commit.

ISO SHA-256:
`4dd9de7a38c4f0d745c2fb74bfdb63e552c372211e5274961814fd9b3d7d22b9`.
Download the desired assets into one directory and run `sha256sum -c SHA256SUMS`.
The full [H13 G1 audit](H13.md), [VM testing guide](../FOUNDATION-TESTING.md),
[fresh build instructions](../FRESH-BUILD.md), [recovery](../RECOVERY.md) and
[licenses](../../LICENSING.md) remain in the tagged source. Raw unsanitized local
build/test workspaces stay outside Git and were not release assets. The original
local owner-testing export remains unchanged as historical H13 evidence.

Physical hardware, persistence, desktop, agent, voice and graphical installer
are not claimed. Berkeley DB's focused owner-approved coverage and the known
compiler/libc/locale/Expat/live shutdown limits remain visible in the release
notes and H13 evidence. G1 is passed in QEMU/KVM; G2 remains pending.
