# MVP detached UEFI owner boots

The fixed MVP host route preserves the existing two distinct installed-owner
boot/settings receipt contract. It does not introduce a one-boot exception,
change packaged runtime validators or claim G2, BIOS or recovery coverage.

The live-install controller's actual cold source context is
`.local/phase2/native-mvp-installer-1`, containing its self-contained
`installed.qcow2`, real handoff, nine actual finalizer reports, frozen inputs and
completed stopped/no-media cold handoff. `inputs.json` must bind the exact MVP
qualification profile, `g2_eligible:false` and UEFI; `cold.json` must retain the
same profile/classification. Merely creating those names authorizes no boot.
The original disk identity/ctime/SHA, live controller/vault/source hashes, plan,
owner and preserved native reports are all checked before a boot context exists.

Use this separate fixed observation context in the main checked-out repository:

```sh
python3 scripts/host/installed_owner_boot.py run --mvp \
  --context "$PWD/.local/phase2/installed-owner-mvp-uefi-1" \
  --round 1 --handoff ACTUAL_PRIVATE_MVP_HANDOFF
```

The controller requires committed source and quiescent guests, pins the
self-contained installed backing, creates one fresh persistent overlay, and
attaches only that disk plus qualified OVMF. Installer ISO, input/data/build disks
and networking are absent. Existing host reserve/write throttling/continuous
low-space shutdown, owned QEMU/QMP identity and no-replay guards remain intact.
Use the same explicit `--mvp` flag on `capture`, `username`, `password`, `enter`
and `stop` controls. Credentials remain RAM-only through the existing actual
PAM/GDM observer/vault; do not include passwords in arguments or log files.

After the first actual authenticated owner GNOME observation and completed cold
stop, use the same persistent observation overlay for boot2:

```sh
python3 scripts/host/installed_owner_boot.py run --mvp \
  --context "$PWD/.local/phase2/installed-owner-mvp-uefi-1" --round 2
```

Both boots must observe actual GDM password authentication, native owner Wayland
GNOME, installed ext4 UUID/kernel/initramfs and no installer media. Boot1 writes
an explicit owner marker and representative clock preference through the owner's
real session bus/dconf; boot2 reads their persistent state. Two distinct real
boot IDs and unchanged source disk are mandatory. The existing `boot-uefi.json`
and `owner-settings-uefi.json` are published only after both observations and
original companion validation. A separate `mvp-scope.json` binds their hashes and
records `g2_eligible:false`, `bios_tested:false`, `recovery_tested:false`.

Preserve these exact public reports in the MVP native input qualification
namespace for the existing source sealer. A missing/failed observation is not a
receipt; an uncertain round is never restarted automatically. Standard callers
without `--mvp` retain their original source and two-boot/recovery routes.
Trusted host modules can call `installed_owner_boot.configure_mvp()` before
constructing the existing shared vault; no path or profile inference is accepted.
