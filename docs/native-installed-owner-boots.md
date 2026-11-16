# Current installed-owner boot controls

These source-only controls execute the first normal GNOME owner boots of the
actual B12 disposable install. They replace neither the installer nor final
release acceptance. The coordinator remains the only VM writer. Source fixture
tests are not native boot/login/firmware evidence.

First finish the real install, collect its actual volatile reports with
`installer_collect.py`, and stop/reconcile the installer VM. Preserve its journal,
review, signed inputs and installed handoff before shutdown. The fixed cold host
disk is `.local/phase2/native-installer-1/installed.qcow2`: an owner-owned 0600
regular single-link file in an owner-owned private 0700 directory, self-contained
qcow2 with exactly 64 GiB virtual capacity and no backing chain. Its actual serial
must be `TODDY-INSTALL-P2-1`. The saved public installed handoff is a separate 0600
file; it contains no password. The helper records its actual SHA plus full source
disk SHA/identity, and rejects candidate/accepted disks as source paths.

Run from the committed checkout as the normal development owner. Choose a new
private context under `.local/phase2/installed-owner-<generation>`; never reuse a
partial context or an uncertain round. The helper holds the existing native boot
lock, refuses running project VMs and rechecks accepted foundation/B02 backings.
It preserves an absolute 100 GiB + 512 MiB host floor and admits each boot only
with the actual cold source's `st_blocks * 512` allocation plus another 2 GiB
above that floor. Virtual capacity is not treated as expected boot writes.
This host admission does not replace the image pipeline's
16 GiB target reserve. The original installed disk is mounted read-only into the
networkless, capability-free, read-only Docker QEMU environment. A single fresh
persistent overlay is writable. Its virtual disk writes are throttled to
16 MiB/second. The owner controller checks host free space every 0.5 seconds,
at startup, after boot and at each input/capture boundary. Within 1 GiB above
the absolute floor it requests powerdown of the exact owned VM, waits up to
5 seconds, then uses the existing label-checked stop/reconciliation path.
Capacity-stop intent is durable and cannot yield an accepted boot or be replayed.
The margin allows for the throttle, polling, QMP deadline, owned stop delay and
qcow2 allocation metadata; it does not promise a bound on unrelated host writes
or an unavailable/hung Docker/kernel. This measured allowance is for boot,
login and the single explicit marker only: no bulk workloads, network or shell
command control are enabled by the harness. A capacity failure preserves the
source and uncertain overlay for coordinator review; it never lowers the floor.
Normal rounds attach only that OS disk, plus
hash-pinned OVMF pflash when UEFI is selected by the real handoff. There is no
installer ISO, build disk, seed, data disk, external kernel or network.

In one terminal start the first round, substituting actual absolute paths:

```text
python3 scripts/host/installed_owner_boot.py run --round 1 \
  --context /actual/checkout/.local/phase2/installed-owner-bios-1 \
  --handoff /actual/private/installed-handoff-actual-operation.json
```

The controller remains running while the guest waits for actual authentication.
In another terminal use `capture --context SAME_CONTEXT`. Inspect the emitted PPM
frame and native boot state. Only after identifying the actual username/password
field use `username`, `enter`, `capture`, `password`, and `enter` as appropriate,
each with that same context. Every private text action requires a captured frame
for its current round. `password` uses a non-echoing interactive getpass prompt;
never pass a credential in command arguments, files, environment, screenshots or
chat. The supported QMP keyboard alphabet is letters, digits, underscore, space,
hyphen, dot, slash and equals; use the actual reviewed disposable owner's
compatible test password and keyboard layout. Unsupported characters fail before
any character is sent. No password, raw QMP request or typed key payload is
persisted. The limited `up`, `down`, `escape`, `tab`, `enter` and `tty` actions
are explicit navigation; QMP acknowledgements never count as authentication.
The `stop` action records durable stop intent, requests bounded graceful
powerdown and stops only the exact label/mount/command-checked owned container.
A stopped round cannot be accepted or replayed as a successful boot.

A public read-only firmware credential starts the existing qualification unit.
It observes the unchanged native default boot; it does not install a service,
reset a password, add autologin, change the default target or select a kernel.
The observer verifies actual ext4 root UUID, the sole OS disk/serial, running
kernel and installed kernel/initramfs/GRUB hashes. It waits for the fresh owner's
active local `gdm-password` Wayland user session and a GNOME shell process under
that UID. Only then it forks, drops all supplementary groups/root identity and
creates the explicit owner-only 0600 `.toddy-install-proof-<operation>` marker
in that owner's home. This is the observer's sole installed-file write. Actual
normal OS boot/login writes are expected and remain on the disposable overlay.
Its dedicated serial observation causes the qualification unit to power off.
The controller preserves unique serial/observation logs, source/input hashes,
stopped-container state and exact overlay identity. Failures/timeouts preserve
intent and context for inspection; they cannot be restarted through this tool.

After round 1 has an actual successful `round-1.json`, run `run --round 2
--context SAME_CONTEXT` without a new handoff. This boots the same persistent
overlay from a stopped VM and requires another actual owner login. It reads the
existing marker as the owner without rewriting it. The controller requires a
different real boot ID and equal measured marker/root/initramfs identity before
writing `boot-bios.json` or `boot-uefi.json` in the strict existing composition
schema. Both reports are observed measurements, never fixtures or prefilled
login assertions. The same private overlay cannot be substituted between rounds.
For the other firmware, perform another real blank-disk install and preserve its
own cold disk/handoff before using a separate new boot context. Keep the first
cold source and context in coordinator custody before replacing the fixed source
with the second real install; never attempt more rounds on the replaced source.

Round 3 is **separate text recovery observation**, after successful rounds 1/2:
`run --round 3 --context SAME_CONTEXT`. During the actual GRUB menu use captures
and explicit navigation to select the installed `Toddy text recovery` entry;
there is no automatic boot-argument override. Authenticate as the fresh owner at
the real text login (the `tty` action selects VT2 if needed). The observer requires
an active local owner `login` tty session, the actual
`systemd.unit=multi-user.target` command line, active multi-user target, inactive
GDM, and unchanged owner marker/root/kernel/initramfs/GRUB. It writes a separate
`round-3.json` with `recovery_only: true`, never a third normal boot row. This
proves the installed text route only. A damaged-root/external-rescue scenario,
failed-update recovery, cancellation and graphical installer qualification remain
separate required tests; this tool does not fabricate them.

Inspect all actual reports and screenshots before copying the firmware boot
receipt to the fixed composition `qualification/boot-<firmware>.json`. Preserve
its surrounding inputs, source identity, container state, all round logs and
recovery report as evidence. The existing sealer still verifies the nine native
finalizer reports, exact signed/image/source inputs and both boot pairs. No
controller result marks production or physical-machine acceptance. Release
handoff still needs the actual ISO/checksum, complete install/privacy/license and
recovery evidence, and clearly pending physical owner validation.
