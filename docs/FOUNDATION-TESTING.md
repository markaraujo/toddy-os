# Owner testing: Toddy OS foundation

This is the H13 command-line foundation handoff. Check status.json for the actual
G1 acceptance state. It contains Linux, native GNU tools, Systemd, networking,
Dpkg/APT and a volatile live root. The desktop, agent, local inference, voice,
memory, automation and graphical installer remain Phase 2; they are not present
in this ISO. The owner requested testing after H13 before any B story begins.

## Artifact and verification

The first public [foundation prerelease](https://github.com/markaraujo/toddy-os/releases/tag/v0.1.0-foundation.1)
contains the same ISO and a release-specific SHA256SUMS. Download its ten assets
into one directory and run `sha256sum -c SHA256SUMS`. The command below uses the
local owner-testing export path; when using a downloaded ISO, set `toddy_iso` to
its absolute path instead. See [publication evidence](evidence/H13-github-release.md).

The verified owner-testing export is outside Git at:

```text
.local/releases/toddy-foundation-2026-11-07/
  toddy-foundation-x86_64.iso
  SHA256SUMS
  components.json
  source-inputs.json
  SOURCE-SHA256SUMS
  source-archives.tar
  toddy-source-history.bundle
  native-build-evidence.tar.gz
  test-evidence.tar.gz
  START-HERE.txt
  release-summary.json
```

G1 passed; see [the requirement audit](evidence/H13.md). An export is complete only when its release-summary.json, full checksums and
separate G1 evidence exist. The ISO is **1,095,000,064 bytes**, SHA-256:

```text
4dd9de7a38c4f0d745c2fb74bfdb63e552c372211e5274961814fd9b3d7d22b9
```

There are **134 image components** and **142 corresponding source archive/patch
inputs**. The source bundle is read back and every member independently matched
to the inventory hash. Native package records bind recipes, source hashes,
archives and notices. The Git bundle preserves the committed implementation
history, including earlier recipe revisions. Build-host images, book archives
and other temporary-build inputs can be acquired from the frozen locks using
[FRESH-BUILD.md](FRESH-BUILD.md); this is not a complete offline host bootstrap.

Before use, from the export directory run `sha256sum -c SHA256SUMS`. Consult
[H11 evidence](evidence/H11.md) and the actual [boot/recovery matrix](evidence/H12-final-media.json).
The old first ISO ending in SHA `...96e41` is retained failure evidence and must
not be substituted: its USB discovery was corrected in ADR-0101.

## Start an isolated interactive console

On the measured workstation, from the repository root, use the existing QEMU
image and KVM access. This command attaches only the verified ISO, with no hard
disk, host home, repository directory or physical disk available inside the VM:

```sh
toddy_iso="$PWD/.local/releases/toddy-foundation-2026-11-07/toddy-foundation-x86_64.iso"
sha256sum "$toddy_iso"
docker run --rm -it \
  --user "$(id -u):$(id -g)" --cap-drop=ALL \
  --security-opt=no-new-privileges --read-only \
  --device /dev/kvm --group-add "$(stat -c %g /dev/kvm)" \
  --memory 5g --cpus 2 \
  -v "$toddy_iso:/media/toddy.iso:ro" \
  toddy-qemu:h01 qemu-system-x86_64 \
  -enable-kvm -machine q35 -cpu qemu64 -smp 2 -m 4096 \
  -display none -serial mon:stdio -no-reboot \
  -object rng-random,id=rng0,filename=/dev/urandom \
  -device virtio-rng-pci,rng=rng0 \
  -netdev user,id=n0 -device virtio-net-pci,netdev=n0 \
  -drive file=/media/toddy.iso,media=cdrom,readonly=on,format=raw -boot d
```

Allow the normal GRUB entry to boot. The verified live profile logs in root on
its local console automatically; the root password stays locked. There is no
published password or imported SSH/API credential. QEMU user networking has no
inbound host forwarding. For offline testing replace the -netdev/-device NIC
arguments with `-nic none` and add Docker `--network=none`.

The automated matrix also verified UEFI and virtual USB; exact QEMU arguments,
private OVMF handling and serial hashes are in the linked evidence. Secure Boot
and real hardware were not tested. The 4 GiB live RAM/2-vCPU setup above matches
the tested profile. The lower-memory limit has not been established.

## What to try

At the Toddy shell:

```sh
cat /etc/os-release
uname -r
findmnt /
findmnt /run/toddy/media
findmnt /run/toddy/lower
systemctl --failed
networkctl status
resolvectl status
getent ahostsv4 example.org
dpkg --audit
apt-get check
printf 'This session is volatile\n' > /root/owner-test.txt
cat /root/owner-test.txt
cat > /tmp/hello.c <<'C'
#include <stdio.h>
int main(void) { puts("Hello from Toddy OS"); return 0; }
C
cc -Wall -Werror /tmp/hello.c -o /tmp/hello
/tmp/hello
ldd /tmp/hello
LC_ALL=pt_BR.UTF-8 locale
systemctl poweroff
```

Repeat the same QEMU command: `/root/owner-test.txt` must be absent. Writes,
package installs and configuration changes live in RAM and do not survive
shutdown. No persistent installed system is claimed. The tmpfs upper layer is
capped at half the guest RAM; inspect `df -h /run` before large changes.
Dpkg/APT are the source-built native tools for Toddy's own packages, not a claim
of Ubuntu/Debian binary compatibility or an active public package repository.

To test rescue, select "Toddy OS early recovery shell" in GRUB. Inspect
`cat /proc/cmdline`, `cat /proc/mounts`, `blkid` and `readlink /proc/1/exe`.
That shell intentionally loops if exited. In QEMU's stdio multiplexer press
Ctrl-A, then X to stop only that VM; restart from the verified original ISO.
The automated missing/corrupt-media tests already proved rejection before a
live root starts, followed by successful normal boot. Never bypass a bad hash
or attach a physical workstation disk as a recovery experiment.

## Known limits and evidence boundaries

- VM-only foundation: BIOS/UEFI CD/USB passed in QEMU/KVM, not on physical hardware.
  Wi-Fi, NVIDIA acceleration, audio, suspend, Secure Boot and dual boot are not
  supported claims from these tests. Missing regulatory.db is retained in logs.
- Shutdown powers off successfully but reports the read-only lower loop/media
  still busy. No writable persistent disk is attached; full initramfs teardown
  and installed-system recovery are separate later work.
- Berkeley DB uses the owner-approved focused production/APT recovery validation
  (ADR-0092). Earlier full Tcl suites remain failed/cancelled, not passed.
- Original GCC/Binutils/Glibc test outcomes and exact source-backed qualifications
  remain in H07 evidence. Native namespace follow-ups are separately recorded in
  H12; other unsupported feature/dependency tests are not relabelled as passes.
- APT cache corruption can emit error diagnostics while apt-ftparchive exits zero.
  Reject diagnostic-bearing index generation and rebuild disposable caches from
  verified packages as in ADR-0092; an exit-code-only wrapper is insufficient.
- English/Portuguese checks passed. Gawk's default matcher and Bash retain the
  exact Greek case-folding limitations documented in ADR-0037; the tested Gawk
  GNU matcher option works for those cases. No universal locale guarantee.
- Expat's unresolved upstream issues remain visible. The final image's XML
  consumers were enumerated and trusted DBus configuration/bounded rejection
  tested. General CLI/library use is not automatically sandboxed; new desktop,
  agent and installer entry points need their own bounds before Phase 2 release.
- The owner approved MIT for original code and CC BY 4.0 for original
  documentation/artwork (ADR-0104). Each third-party component retains its own
  license; no blanket whole-OS relicense is implied. The VM-only testing limits
  apply equally when a public prerelease is available.
- Checkpoints are local to the same workstation storage, not an off-host disaster
  backup. [RECOVERY.md](RECOVERY.md) describes exact retained states and failed runs.

The next authorized action after H13 is owner testing and review. B01–B13 remain
not_started until explicit approval; a completed foundation is not the complete
experimental desktop/agent/installer release.
