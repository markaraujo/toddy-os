# ADR-0141: Reclaim free blocks in the mutable virtual target overlay

- Date: 2026-11-08
- Status: Accepted; actual native maintenance and full content comparisons passed
- Inputs: Phase2 mutable KVM overlays, immutable post-H13 backing receipt,
  designated193273528320-byte TODDY-LFS-TARGET disk; ADR-0110/0135

The target has376MB headroom above its16GiB reserve; the development host has
about1.62GB above its100GiB reserve. The frozen BLFS13.1 Glycin section needs
approximately1.4GB plus1GB for tests. Preserve reserves and qualified caches.
Do not resize/format any disk or restart accepted compiler/test work.

Enable QEMU discard=unmap only on the mutable Phase2 target QCOW2 drive. The
foundation mount/backings remain read-only and the existing identity/startup
guards remain required. Cleanly stop/restart only the designated VM after every
writer is terminal. Preserve the serial log and exact maintenance checkpoint.
This changes virtual free-block handling, not installed files or physical-host
device configuration. No global security setting or guest isolation flag changes.

Before shutdown, use the unchanged full-root package snapshot plus the complete
pending Libadwaita work/cache snapshot. Retain private manifests and a persistent
maintenance state receipt. On the new boot verify target identity and restore
the same three scratch filesystems only after UUID/inode/size/path/empty-underlay
checks; never recreate or format them. An existing correct mount is verified
instead of repeated. Require advertised virtual discard support, then fstrim
only the guarded virtual /mnt/lfs filesystem once.

Record the real exit/log and compare complete target and pending-cache contents
and ownership/modes against the checkpoint. Measure actual host available space
separately; a trim message alone does not prove reclamation. Any interrupted or
verification-failed state is reconciled, never replayed to hide failure. Keep the
failure budget/input identities across resumption. No physical machine, graphical
acceptance or completed Phase2 release is implied by this maintenance operation.

The clean shutdown/cold QCOW2 checks/restart succeeded. Target discard exited0,
reclaimed685,936,640 allocated bytes in the mutable image, and preserved all
140,102 full-root entries plus1,111 pending Libadwaita cache entries. All three
original scratch filesystems were restored by matching UUID/inode/size/backing.
Separate source-only custody then verified every expanded byte against retained
archives before retirement, preserving compressed Cargo caches and all compiled
artifacts. Actual measurements and limitations are in the maintenance/custody
evidence. Never replay either completed operation.
