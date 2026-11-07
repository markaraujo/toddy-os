# ADR-0096: Build media dependencies at their first live-system use

- Date: 2026-11-07
- Status: Native media dependencies and actual H10 BIOS/CD console validation passed
- Amends the tool-installation ordering in ADR-0050/0077/0082, not release gates

## Problem and decision

H10 must demonstrate actual root discovery and volatile writes in a guest.
Its reviewed initramfs discovers a hash-bound ISO filesystem. The prepared
recipes placed Mtools/libburn/libisofs/libisoburn installation behind completed
H10, creating a cycle for the first complete live test. H09 now supplies an
accepted production kernel and actual BIOS/UEFI boot; resolve the dependency
order before assembling H10, without claiming H11 early.

Build and verify the frozen native media utilities when H10 first needs them.
A dedicated dependency gate requires H09 completed, its actual kernel/loader
success records, and active H10 or H11. Only the eight tool recipe/postcheck
entry points use it. Keep the H11 release gate unchanged for release assembly,
credential review and QA removal. Existing `h11-*` per-package step identifiers
remain stable; these identifiers do not mark the H11 milestone completed.

The shared ISO composer gains an explicit `--validation` mode requiring active
H10 and a successful H10-profile root/compression/initramfs binding. The default
still requires active H11 and the distinct release profile. Both modes require
the actual installed native media packages, unchanged payload/archive identity,
full ISO readback and kernel/module consistency. Every result records
`validation_only`; neither mode declares release or boot acceptance.

Correct the composer's exact GRUB package version from `2.14-1` to the accepted
H07 metadata revision `2.14-1+toddy1`. The upstream source/binary version remains
2.14. Do not accept arbitrary versions or remove native package ownership checks.

## Validation strategy

Use the real live serial console, source-built agetty/Shadow/Bash login and
Python test payload in a separate BIOS/UEFI CD/USB QEMU guest. No diagnostic
service replaces the login path. Check overlay/tmpfs and read-only media/lower
mounts, an actual volatile write, package consistency, native C compilation,
Kmod lifecycle, active services, and DHCP/resolved DNS or explicit offline boot.
Test commands contain no credentials and fit the terminal's canonical input
limit. Preserve serial logs, native report, exact QEMU arguments, command/probe
hashes and actual power-off status. Test containers are identified individually;
only their own writable workspace and read-only ISO are attached.

H10 validation media remains private and includes its development profile.
H11 must generate a fresh release profile after the required QA/credential
review. H12 must test that final artifact; an H10 success cannot be reused as
an untested final-ISO pass. H13/G1 and the owner review boundary are unchanged.

## Alternatives and sources

Reusing the completed private Mtools/ISO prefixes would work experimentally,
but would require separate bootstrap provenance and duplicate the clean-build
procedure. Installing new host ISO utilities would test a different toolchain.
Marking H10 complete before live boot would violate its acceptance criterion.
Build each production dependency once at its actual first use instead.

Sources reviewed: frozen BLFS 13.1-systemd `postlfs/initramfs.html` describes
kernel/initramfs loading and root setup; its `multimedia/libburn.html`,
`libisofs.html` and `libisoburn.html` give the selected source-build recipes.
ADR-0047/0048/0050/0077/0081/0082 record frozen tool versions, native archive,
ACL and hybrid-media experiments and the explicit live-root deviations.
No source version, compiler/libc test, release criterion or security control
is removed by this ordering correction.
