# ADR-0101: Probe kernel block nodes explicitly for hybrid live media

- Date: 2026-11-07
- Status: Native cause reproduced; complete corrected boot verification pending

H12's exact H11 ISO booted and logged in through BIOS/CD and UEFI/CD. BIOS/USB
reached the selected kernel but failed media discovery and opened the recovery
shell. The original failing serial log and a separate diagnostic boot remain
preserved; neither is a successful USB boot.

Actual recovery-shell evidence: automatic `blkid -c /dev/null` lists sda1/sda2/
sda3, but no ISO filesystem. Explicit `blkid -p -o export /dev/sda` reports both
TYPE=iso9660 and PTTYPE=gpt. A read-only ISO mount of the whole sda succeeds and
reads the exact embedded media identity. This is enumeration, not a missing
storage driver, bad hybrid layout or digest mismatch.

Frozen Util-linux **2.42.4** misc-utils/blkid.8.adoc states that automatic discovery
shows partitions or unpartitioned devices. Explicit --probe bypasses the cache;
-s TYPE filters the returned tag, and ambiguous probes return nonzero. Source
SHA-256: ca72ae2ca4d2b80dac3767db1094a5cf7fd523565f7302b0fc13c542fbde4bb6.
The selected archive remains in the committed source lock; no version changes.

Enumerate /sys/class/block kernel nodes, constrain names, require a direct block
node in devtmpfs, then run `blkid -p -s TYPE -o value DEVICE`. Require exit zero
and exactly iso9660. Retain read-only/nosuid/nodev/noexec mounting, exact embedded
identity, complete compressed-root SHA-256 and all overlay/ACL checks. No labels,
filenames or arbitrary probe output become authorization or shell commands.

Alternatives rejected: hard-code sda (breaks other virtual devices), remove the
hybrid partition table (breaks required UEFI/USB layout), or bypass content
verification (weakens acceptance). The existing minimal native blkid suffices;
no additional initramfs tool or package is needed.

Only initramfs and ISO need regeneration; accepted root, compression, packages
and their reports remain unchanged. Reopen H11 during artifact replacement,
then repeat the complete H12 matrix against its new exact SHA. Preserve the
first artifact and both USB failure logs. The host console harness now fails
promptly on TODDY_LIVE_ERROR rather than waiting for the full login deadline.
