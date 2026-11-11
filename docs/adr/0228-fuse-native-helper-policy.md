# ADR-0228: Exact native FUSE helper privilege policy

- Date: 2026-11-11
- Status: Accepted implementation decision; native mount/privilege acceptance pending

The selected desktop portal closure needs source-built Fuse3.18.2 and the matching
Linux7.1.8 module. Frozen BLFS13.1 postlfs/fuse.html explicitly installs
fusermount3 root SUID. Register only fuse:/usr/bin/fusermount3, root:root,4755,
source package3.18.2-1+toddy1 in the existing ownership exception policy. The
normalizer still rejects build-owned privileged files, wrong identity/mode and
all other undeclared privileged paths. Native staging creates this permission
explicitly after verifying the unprivileged compiler-stage hash.

The exact source archive SHA256 is
f01de85717e20adf5f98aff324acd85dd73d61a5ca3834d573dcf0bd6e54a298.
Source util/fusermount.c has check_perm at1094/call1292, default user_allow_other=0
at56 and owner guard991, and initial MS_NOSUID|MS_NODEV flags926. These are a
narrow source review, not a whole-code security audit. Preserve the default
owner-only configuration; actual ordinary-user mount, other-user denial,
allow_other refusal, signals, unmount and recovery are required in the native
reference guest before accepting this capability. CLI/ABI tests alone do not
prove those behaviors.

The installed owned Systemd261.2 FUSE0666 device rule and separately owned kernel
module remain responsible for the device. Host devices/security are unchanged.
The first package attempt was blocked by the central ownership policy before
archive/native install. Inspect its actual absent archive/package/control state,
then resume only verified promotion/package creation; do not compile again.

References: frozen BLFS13.1-systemd postlfs/fuse.html; exact Fuse3.18.2 LICENSE,
util/fusermount.c and pinned source lock; ADR0039 package ownership normalization;
ADR0110 isolated compiler/staging and controlled native transactions.
