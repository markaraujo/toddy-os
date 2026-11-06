# ADR-0052: Stage early userspace from verified native package files

- Date: 2026-11-06
- Status: Private native runtime experiment passed; live boot integration pending

The frozen BLFS 13.1 postlfs/initramfs.html describes an early shell runtime
with its program/library dependencies. ADR-0047 selects already-built native
Libarchive for newc packaging. Prepare an explicit small runtime using our
accepted native programs rather than copying the builder's configuration or
introducing another shell/tool implementation. This does not dispatch H10 or
replace its H09 prerequisite.

The helper scripts/build/h10/initramfs_runtime.py selects eleven programs from
the installed native Dpkg inventory. Before staging, it checks configured
package ownership, recorded archive provenance and exact installed file hashes.
It asks the native loader for each verified program's transitive dependencies,
rejects unexpected output or unresolved libraries, and verifies their owners
and bytes as well. Canonical source resolution handles merged-/usr aliases;
the private runtime has explicit aliases and regular library bytes at the
required loader/SONAME paths. Conflicting destination content is refused.

Only declared executable/library directories may supply payload. No account,
credential, home, builder mount, firmware or optional module tree is copied.
The new private stage has fixed console/null device nodes and root-owned
payload without set-ID bits. This early-root policy does not change the full
system's service identities, ACLs or privileged helper metadata. Existing or
redirected stages and destinations outside target staging/private temporary
storage are refused before package queries or writes. Production invocation
requires the existing H10 gate and a fixed target staging path.

A real private chroot assembled twenty files from eight accepted packages:
Bash, Coreutils, Glibc, Ncurses, OpenSSL, Readline, Systemd and Util-linux.
Native shell, program version execution, directory/file creation, readback,
SHA-256, link reading, sleep and null-device writing passed with exit 0.
Console/null types and absent account/source/tool trees were checked. The
fixture was removed; no installed package or active build input was changed.
Three local tests cover path confinement and preservation before mutation.

Evidence: .local/logs/h10-native-runtime-bundle-probe.log, SHA-256
`141ec5fc3ac9878f2215de2ffdc9c2835a0b8ac7e27c161a749aac4bedb6e783`.
The tested helper SHA-256 is
`d9d80ee389a2b20329ace280186f89c3a00b5dc7bfeca234ec7166c329810d3d`.
The log retains per-file package/version/archive/content hashes.

Alternatives were a whole-root copy (unnecessary state and payload), another
minimal tool suite (additional source/build/behavior to qualify), or unchecked
host loader discovery (wrong provenance). Native package ownership provides
an auditable dependency boundary using tools already accepted in H07.

The loader listing does not prove optional dlopen modules or data coverage.
There is no /init, live root, overlay or bootable initramfs in this experiment.
Actual device discovery, early mounts, root selection, overlay setup, ACL
restoration before services, failure diagnostics and native-kernel boot remain
mandatory. No H10 acceptance credit is assigned to this preparation.


## Private PID-1 root-switch experiment

The accepted native Util-linux 2.42.4 sys-utils/switch_root.c moves /dev, /proc,
/sys and /run, changes the root mount, forks old-root cleanup for ramfs/tmpfs,
and executes the selected init. Verify that behavior with the exact minimal
runtime, not only its --version output. The reusable host experiment is
scripts/host/probe_switch_root.py.

The designated builder creates a private mount namespace with private
propagation and a private PID namespace. Its initial and final roots are on
two distinct 128 MiB tmpfs mounts, each populated from the verified native
runtime. Distinct device IDs are asserted before invoking switch_root: its
old-root removal must not traverse the new root. No installed or physical root
is a switch/removal target. A private /dev tmpfs contains only console/null;
/run is another private tmpfs, and proc/sysfs are mounted inside the namespace.
The sysfs mount is read-only for this fixture, not a proposed product setting.

The native shell enters as PID 1, writes a /run marker and execs switch_root.
The final native shell is still PID 1, sees the final-only marker and the four
moved mounts, reads the original /run bytes, accesses the two character devices,
and observes /proc/1/root as /. Original-root/source/tools/account files are
absent. It exits 0; the parent confirms the private tmpfs mounts disappeared
with the namespace and removes only the resulting empty fixture. The launcher
uses unshare --kill-child=KILL so controller death kills its namespace child;
the positive run, not a forced-timeout scenario, was exercised here.

An initial harness incorrectly invoked /usr/bin/env inside the intentionally
minimal runtime and failed 127. Clear the process environment with execve before
entering that root instead; do not expand the payload to satisfy an unnecessary
test assumption. Original failure evidence is
.local/logs/h10-native-switch-root-missing-env.json, SHA-256
`2585fc4713aa2d37797792ae3c2cd37656bcb9558fdc0801482ab3763cb3f40d`.
Its empty private fixture was inspected and removed after the namespace exited.

The final repeated positive evidence is
.local/logs/h10-native-switch-root-probe.json, SHA-256
`78148992f466879ab96b4dc2f404e1118f1dad9467d13b0698906bb378c585fc`.
It uses the builder's 6.8.0-147-generic kernel. No initramfs archive was booted,
no Squashfs/overlay was the switched root, and Systemd was not the test init.
Those actual native-kernel/live-media/service checks remain mandatory. The
fixture /init is test code only and is not the pending product live-root loader.
