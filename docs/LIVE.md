# Toddy OS foundation live media

This is the Phase 1 command-line foundation, not the planned graphical desktop
or installer. H13 is an interim owner-testing delivery. Phase 2 requires the
owner's explicit approval after that review. Physical hardware support remains
untested unless the release test matrix records an actual result.

Current verification: the revised foundation ISO passed actual BIOS/UEFI boots
through both CD-ROM and virtual USB, including offline USB, real console login,
volatile writes, native C/Kmod and package checks. Actual GRUB recovery, absent
media, corrupted-root rejection and subsequent intact-media boot passed. See
[evidence/H12-final-media.json](evidence/H12-final-media.json). H13/G1 acceptance
is a separate recorded gate. The native guests power off with exit zero but
Systemd reports its read-only lower loop/media busy during final shutdown;
complete initramfs teardown and persistent-disk behavior are not claimed.

See [FOUNDATION-TESTING.md](FOUNDATION-TESTING.md) for the local artifact layout,
interactive QEMU command, owner checklist and known limitations.

## Boot and console

Use the artifact path and SHA-256 from its generated manifest. Verify the hash
before attaching it to a disposable QEMU VM. The validation harness records
exact QEMU arguments and serial output; use `scripts/host/live_boot_test.py`
with the applicable H10 or H12 milestone gate. Do not use validation media as
a qualified H13 release. BIOS and UEFI, CD-ROM and virtual USB require their
own actual recorded boot results.

The normal GRUB entry passes `toddy.live`. Early init discovers an ISO filesystem
and verifies its embedded media identity and compressed-root SHA-256. It mounts
the medium and Squashfs read-only, creates a tmpfs-backed writable overlay,
restores declared ACLs and starts native Systemd. An unmatched or corrupted
medium must not become the live root.

The foundation profile provides automatic root login on tty1 and ttyS0 only
when the verified early init has created its runtime live marker. The root
password remains locked. No SSH key or builder account is copied. This local
administrative console is intentional for disposable foundation testing; do
not infer installed-system authentication or remote login support from it.

## Files and persistence

Writes go to the in-memory overlay. Files created in /root, configuration edits,
package installations and logs disappear when the VM shuts down. The compressed
root and ISO do not change. Reboot with the same ISO starts a fresh session.
There is no persistent live volume or graphical installer in this delivery.

The runtime tmpfs is capped at half the VM's RAM. Large downloads, builds and
package changes can exhaust it before the VM runs out of disk space. Check
`df -h /run` and `free -h`. Copy wanted logs to separately designated storage
before shutdown; never select a physical host disk as a testing target.

## Diagnostics and recovery

Use `uname -r`, `findmnt /`, `systemctl --failed`, `journalctl -b`,
`networkctl status` and `resolvectl status` after login. Network availability
requires a supported virtual NIC, DHCP and a working upstream resolver. Offline
boot is tested separately from networking; no hosted service is needed for the
base shell, compiler or package inventory.

Early init prints `TODDY_LIVE_ERROR` and opens a local recovery shell when
media discovery, hash validation, overlay setup or ACL restoration fails.
The GRUB recovery entry adds `toddy.rescue`, requesting that shell before root
assembly. Inspect `/proc/cmdline`, `/proc/mounts` and `blkid`; preserve the serial
log and exact artifact hash. No verified-medium message means the root was not
accepted. Do not bypass a checksum failure: verify or rebuild the artifact.

The recovery shell is inside the minimal initramfs; it is not a full desktop or
installer and does not automatically modify disks. Exit returns to the recovery
shell loop. A disposable VM can be stopped after preserving its logs and booted
again from the original verified ISO. See [RECOVERY.md](RECOVERY.md) for retained
build generations, cold checkpoints and exact failed-step procedures.
