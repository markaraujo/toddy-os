# ADR-0008: Native source-built .deb packages and explicit ownership

Date: 2026-11-05
Status: Accepted after H03 disposable-root prototype

## Decision

Use dpkg's .deb format and ownership database for Toddy OS's own source-built
final packages. Build dpkg and subsequently APT from frozen upstream sources;
operate only a project-controlled, signed native repository for host packages.
Do not configure Debian/Ubuntu binary repositories in Toddy OS. Builder-host
dpkg is tooling only and may initially populate the target package database
with project-built, staged packages; its binaries are not copied into release.

Resolve this before final recipes: install to DESTDIR (or the package's
equivalent install_root), record staged files, inspect ownership/conflicts,
then create and install the native archive. Stage paths must not leak into
runtime ELF/interpreter metadata. No foreign dependency resolution or package
maintainer scripts are imported. Model post-install system integration
explicitly. Keep conffiles separate, explicit package dependencies and
versioned component/source/license metadata. APT's signed-index and solver
behavior must pass later package/update acceptance before release.

The temporary toolchain is build infrastructure: follow LFS's direct prefix
installation and keep before/after content manifests and logs. Before H07,
remove temporary-system ambiguity using the book's cleanup/checkpoint and
assign final installed payloads to native packages. Do not infer ownership
from timestamps. Direct final installations outside the package system require
an explicit exceptional recipe and ownership import, never silent omission.

## Prototype and recovery

scripts/build/package-prototype.sh built test .debs in a temporary root in the
KVM guest using builder dpkg 1.22.6. It passed install, ownership lookup,
upgrade, user conffile preservation, file conflict rejection, missing
dependency rejection, full-root/database rollback, remove and purge.
No distro binary package was installed into that root or the LFS target.

The experiment showed dpkg can unpack an update before a dependency failure;
it is not a transaction-wide rollback engine. Require dependency planning,
package cache, complete checkpoint and recovery before a production update.
A copied root on the same disk is not disaster recovery. Later tests must
exercise rollback of a bootable installed guest and signed repository failure.
Do not use --force-overwrite to mask conflicting package ownership.

## Alternatives

A new custom package manager increases untested security and update surface.
Timestamp-only tracking misses preserved timestamps and concurrent writes.
Symlink-per-package trees risk nonstandard linker paths and cannot safely
cover the entire base. Existing dpkg provides well-established file ownership
and conffile handling, but Toddy owns integration and ABI compatibility.

## Sources

Frozen LFS 13.1-systemd section 8.2 (package management techniques and
DESTDIR), sections 4.2–4.4 (temporary environment); installed dpkg 1.22.6
manual/help in the disposable Ubuntu builder; actual prototype evidence in
[H03](../evidence/H03.md). This ADR does not claim APT or dpkg is already
source-built or available in a Toddy release.

## Staged merged-/usr adaptation, 2026-11-05

The real final Glibc staging experiment installs ldconfig/sln into a physical
/sbin directory when its DESTDIR is empty. The book's live target instead has
/sbin -> usr/sbin, so a direct install naturally reaches /usr/sbin. The
packager rejected the noncanonical staged alias before any target mutation.
Canonicalize staged bin/lib/sbin directories into usr counterparts before
ownership checks, preserving file metadata and rejecting duplicate payloads.
This reproduces the selected target namespace; it does not change configured
runtime paths. Keep the failed stage/log and repeat staging only, not the
already accepted critical suite. Record the packager hash with the archive.
