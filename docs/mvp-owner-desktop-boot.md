# Ordinary owner MVP desktop boot

This is an interactive ISO-only preview, not installer or release acceptance.
It attaches no candidate, backing image, installation disk or host filesystem to
QEMU. The running builder may continue independently. No model/provider is
configured by this boot. Close QEMU to discard the live session.

On the development host, the checked QEMU binary supports KVM, GTK and SDL;
the current owner can read/write `/dev/kvm`. Host OVMF is absent. The existing
pinned `toddy-qemu:h01` image contains the firmware used by `boot_test.py`.
The host has a local graphical session (`DISPLAY=:0`); run the commands as the
ordinary desktop owner, never with sudo. Allocate 4 GiB only when current
`MemAvailable` exceeds 6 GiB, preserving room for the builder.

After the coordinator transfers the **actual complete** MVP desktop ISO and its
native `SHA256SUMS` into the fresh private context below, run from the repository
root. These commands intentionally fail if that context already exists. Do not
substitute an accepted foundation ISO or infer that an absent MVP ISO exists.

```sh
umask 077
mkdir -m 0700 .local/phase2/mvp-owner-desktop-1
```

The coordinator places only `toddy.iso` and `SHA256SUMS` in that context, matching
the successful native `toddy-mvp-release-media-1/result.json`. Then verify the
transfer and obtain public firmware from the pinned utility image:

```sh
(cd .local/phase2/mvp-owner-desktop-1 && sha256sum -c SHA256SUMS)
docker run --rm --network none --read-only --cap-drop ALL \
  --user "$(id -u):$(id -g)" \
  --security-opt no-new-privileges \
  -v "$PWD/.local/phase2/mvp-owner-desktop-1:/work:rw" \
  --entrypoint /bin/sh \
  sha256:8ef60fce7caa9a0b562cba67aac067b92d4a0c40547411184120f20071a633cf \
  -c 'cp /usr/share/OVMF/OVMF_CODE_4M.fd /work/OVMF_CODE.fd && cp /usr/share/OVMF/OVMF_VARS_4M.fd /work/OVMF_VARS.fd'
python3 - <<'PY'
import hashlib, os
from pathlib import Path
work=Path('.local/phase2/mvp-owner-desktop-1')
for name, expected in {
    'OVMF_CODE.fd':'ad23261d43116abc3747d59a7837fbf578c9586a8993f4eeba064cd07eccb083',
    'OVMF_VARS.fd':'5d2ac383371b408398accee7ec27c8c09ea5b74a0de0ceea6513388b15be5d1e',
}.items():
    path=work/name
    assert path.is_file() and not path.is_symlink()
    assert hashlib.sha256(path.read_bytes()).hexdigest()==expected
assert os.access('/dev/kvm',os.R_OK|os.W_OK)
mem={line.split(':')[0]:int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines()}
assert mem['MemAvailable']>6*1024**3
PY
qemu-system-x86_64 \
  -name Toddy-MVP-owner-preview -enable-kvm -machine q35 -cpu qemu64 \
  -smp 2 -m 4096 -display gtk -device virtio-vga \
  -drive if=pflash,format=raw,readonly=on,file=.local/phase2/mvp-owner-desktop-1/OVMF_CODE.fd \
  -drive if=pflash,format=raw,file=.local/phase2/mvp-owner-desktop-1/OVMF_VARS.fd \
  -drive if=none,id=cd,media=cdrom,format=raw,readonly=on,file=.local/phase2/mvp-owner-desktop-1/toddy.iso \
  -device ide-cd,drive=cd -boot order=d,strict=on \
  -nic none -monitor none -no-reboot \
  -serial file:.local/phase2/mvp-owner-desktop-1/serial.log \
  -qmp unix:.local/phase2/mvp-owner-desktop-1/qmp.sock,server=on,wait=off
```

GTK presents the actual VM window on the owner's desktop. For a separate local
VNC client, replace `-display gtk` with `-display none -vnc 127.0.0.1:7`; this
binds only loopback port 5907. No VNC viewer is currently installed. Do not bind
VNC publicly. QMP `screendump` can save the actual graphical framebuffer to a
file inside this context without injecting observer code into the guest.

The source live policy requests GDM automatic Wayland login for `toddy-live`
UID 1000. Both root and that live user's passwords are locked; no password is
required or supplied for the normal live desktop. If GDM instead asks for a
password or fails to start, retain the real screen and serial log and diagnose
the boot; do not invent a credential or bypass PAM. Open Toddy from the desktop
application list. The live Install action remains independently gated by the
actual image/session attribution and installer readiness. This ISO-only VM has
no writable target disk, so installation cannot proceed here.

This ordinary preview does not replace the separately owned blank-disk install,
two persistent UEFI boots, owner settings checks, or recovery evidence. The
runtime overlay and any live-session changes are lost at shutdown.
