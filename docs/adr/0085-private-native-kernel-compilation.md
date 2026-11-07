# ADR-0085: Compile the frozen kernel in a private native fixture

- Date: 2026-11-07
- Status: Native configuration passed; compilation running
- Extends: ADR-0046

## Decision

While the corrected complete Berkeley DB suite runs, extend the existing private
kernel configuration experiment to actual compilation and module staging. Use
the native final compiler, frozen Linux 7.1.8 source and unchanged reviewed
139-option fragment in a fresh protected directory under sources/recovery.
This is independent feasibility work: do not dispatch the H09 package recipe,
install into the target's boot/module directories, modify boot sectors or reboot
the builder. H07 remains the active story; H08/H09 prerequisites and acceptance
are unchanged. A private binary is not an accepted kernel package or boot result.

The frozen LFS 13.1-systemd section 10.3 prescribes clean source preparation,
configuration, make and modules_install. It also explains that retained builds
should preserve object files for incremental rebuilds. Follow those steps with
an explicit private INSTALL_MOD_PATH. Preserve the prior API-header tree and
ADR-0046 configuration experiment. Do not import the builder's kernel config.

Alternatives: waiting leaves independent compiler compatibility unexplored;
dispatching the final recipe would violate its prerequisite gate; building on
the workstation would test a different compiler/library environment. A private
native build exercises the intended inputs without changing installed packages.
It costs additional disk space and must not be mistaken for final packaging.

## Resources and recovery

At launch the 12 GiB builder had 11,167 MiB available, zero swap use and 123 GiB
free on its designated target. Limit make to two jobs, preserving capacity for
database tests and unrelated host workloads. The target identity guard and
10 GiB free-space floor run before work. The source archive is checked against
the frozen SHA-256 before extraction:
ff01dcb449279d5b4cfccdb01fee639cf5ff1803f1749a77844dd33915422c49.

scripts/host/probe_native_kernel.py transfers only private probe inputs, not a
global build-input synchronization. The native driver records per-stage intent,
PID, log hash, timeout and actual exit. Each attempt retains separate logs and
failure evidence. Successful stages have exclusive completion records; resume
verifies their command/log identity and preserves compiled objects. Source,
fragment/checker/driver and installed package database hashes are rechecked.
The fixed build identity matches the prepared production recipe. Byte-identical
reproducibility is not claimed.

The launcher refuses another live fixture and refuses resuming a locked driver
or an unfinished stage whose detached child still exists. A missing supervisor
alone is not permission to restart. A partial extraction remains for diagnosis;
do not delete it automatically. A changed compiler/package environment requires
review rather than silently reusing objects. Final artifact checks require real
x86 Linux/EFI image recognition, exact release/configuration, a staged dummy
module with matching vermagic, artifact hashes and unchanged package status.
They cannot prove successful boot or module insertion.

## Actual evidence

The private driver started at 09:48 UTC. Source verification/extraction and
configuration/preparation exited zero. Native GCC reports 16.2.0; the exact
release is 7.1.8-toddy. The make stage is live and compiling native objects.
No complete kernel image, module-install result or boot is claimed yet.

- Launch report SHA-256:
  65c1320d6a7598389e536d9dc2b1f1e3509efae8f9b1643dcd0c4ab61a17db4f.
- Actual configuration/preparation log SHA-256:
  8018b5bfccb7235f867dc095d61d15564b55031c4bb7743b4ecb3f85775850f1.
- Live collection report SHA-256:
  03df8e3d2f282a69c970c0c213ddfe4a7119a1ae40eb07b860289ff22bfe6818.
- Both native concurrent-start and active-resume attempts refused; report SHA-256:
  59d3eee1d2d961184cade34f72de39d118788e56f732bafb9aa60b3c471c6425.

Raw reports remain in ignored .local/logs/h09-private-kernel-* files. The exact
fixture, PID and next command are in the local checkpoint and recovery notes.
Collect and inspect terminal exits, artifacts and postconditions before any
later claim of successful compilation. Production packaging and complete native
boot tests remain mandatory behind H08/H09.
