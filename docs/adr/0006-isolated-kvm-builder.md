# ADR-0006: KVM build guest with container-packaged QEMU

Date: 2026-11-05
Status: Accepted; guest validation recorded in H01 evidence

## Context

The workstation has 32 logical AMD Ryzen 9 5900XT CPUs, 30 GiB RAM,
758 GiB free on ext4, working Docker 29.9.0 and session access to /dev/kvm.
QEMU is absent and noninteractive sudo requires authentication. Host services
and unrelated workloads must remain intact. LFS requires a known compatible
build host; the workstation is not the LFS target.

## Decision

Package QEMU 8.2.2, firmware and cloud-image tooling in a pinned Ubuntu 24.04
container. Run an actual KVM guest inside it, passing only /dev/kvm and a
project-local VM storage directory. Drop container capabilities; do not use
privileged mode, Docker socket mounts, host networking or physical disks.
Expose SSH on workstation loopback only, using a project-local ephemeral key.
This key and the seed image never enter a release or Git.

Use the official Ubuntu Noble cloud image release-20261017 as the disposable
build host, checking its SHA-256 against the vendor HTTPS SHA256SUMS before
creating an overlay. Ubuntu is build infrastructure, not Toddy OS's parent
system. Allocate 12 vCPUs, 12 GiB guest RAM, 32 GiB builder disk and a separate
180 GiB sparse target disk with serial TODDY-LFS-TARGET. Start compilation at
8 parallel jobs, preserving workstation headroom; measure before increasing.
Keep at least 100 GiB host free and stop expanding images before that reserve
is consumed. Never use host-native CPU flags in release builds.

## Alternatives

Host apt installation requires unavailable sudo authentication. Extracting
QEMU into a user directory complicates dynamic dependency resolution. A
container-only LFS build cannot prove guest kernel/firmware/boot behavior.
TCG is a fallback when KVM is absent, with a substantial performance cost.
VirtualBox remains an untested compatibility target.

## Recovery and consequences

The builder disk, target disk and base are separate files. Stop the guest
cleanly before copying/checkpointing qcow2 images. Preserve the readonly base
and source cache. Never restore a disk under a running QEMU process. Recreate
container tooling from scripts/host/Dockerfile; it does not own persistent
state. Use scripts/host/vm.py for lifecycle and SSH. Package versions are
captured separately for container and guest. No workstation package or sudo
policy is changed. Sparse sizes are capacity ceilings, not reserved storage.

## Sources

- [LFS 13.1-systemd section 2.2](https://www.linuxfromscratch.org/lfs/view/13.1-systemd/chapter02/hostreqs.html), consulted 2026-11-05: host software and compiler bounds.
- [Ubuntu Noble release-20261017](https://cloud-images.ubuntu.com/releases/noble/release-20261017/), consulted 2026-11-05: build-host image and vendor hashes.
- Installed QEMU 8.2.2 command help and actual startup tests; failures and corrections are recorded in docs/errors.md.
