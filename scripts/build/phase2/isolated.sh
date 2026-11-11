#!/bin/bash
# Guest-only compiler sandbox. No installation or native package transaction here.
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
loopback=0
if [[ ${1:-} == --loopback ]]; then
    loopback=1
    shift
fi
[[ $(id -u) == 0 && $# -ge 3 ]] || exit 64
input=$(realpath -e -- "$1")
work=$(realpath -e -- "$2")
[[ $input == "$1" && $work == "$2" ]] || exit 65
[[ $input == /mnt/lfs/sources/phase2/inputs/* && -d $input ]] || exit 65
[[ $work == /mnt/lfs/sources/phase2/work/* && -d $work ]] || exit 65
[[ $(dirname "$work") == /mnt/lfs/sources/phase2/work ]] || exit 65
[[ $(dirname "$input") == /mnt/lfs/sources/phase2/inputs ]] || exit 65
shift 2
exec 9>/var/log/toddy/build/build.lock
flock -n -E 75 9
if compgen -G '/var/log/toddy/build/*.running.json' >/dev/null; then
    echo 'Unreconciled recipe marker; refusing sandbox' >&2; exit 75
fi
uid=$(chroot "$LFS" id -u tester)
gid=$(chroot "$LFS" id -g tester)
[[ $uid != 0 && $gid != 0 && $(stat -c %u "$work") == "$uid" ]] || exit 65
export TODDY_INPUT=$input TODDY_WORK=$work TODDY_UID=$uid TODDY_GID=$gid
export TODDY_PRIVATE_LOOPBACK=$loopback
# New PID/network/IPC/mount namespaces. Only native dependencies and declared
# inputs are exposed; no guest /root, signing material, sockets or host home.
exec unshare --mount --pid --net --ipc --fork /bin/bash -s -- "$@" <<'SANDBOX'
set -euo pipefail
# The outer unshare parent retains the flock. Never expose its writable lock FD
# to source/compiler processes, which could otherwise write/unlock it.
exec 9>&-
[[ $$ == 1 ]] || { echo 'Private PID namespace init required' >&2; exit 70; }
mount --make-rprivate /
# Optional native inference fixture transport. This is the newly created network
# namespace: loopback only, no inherited interfaces or external routes. Compiler
# jobs retain the default down loopback. The child still drops all capabilities.
if [[ $TODDY_PRIVATE_LOOPBACK == 1 ]]; then
    /usr/sbin/ip link set dev lo up
fi
root=$(mktemp -d /run/toddy-build-root.XXXXXX)
# A session daemon can still be closing descriptors after its launcher returns.
# Detach this private tree; PID-namespace init exit terminates remaining children,
# then the outer unshare parent exits and releases all namespace references/lock.
# This sandbox cannot access package databases or writable system payloads.
trap 'result=$?; cd /; umount -R --lazy "$root"; rmdir "$root"; exit "$result"' EXIT
mount -t tmpfs -o size=16m,nosuid,nodev tmpfs "$root"
mkdir -p "$root"/{usr,etc,lib64,src,build,stage,tmp,proc,dev,run}
ln -s usr/bin "$root/bin"
ln -s usr/sbin "$root/sbin"
ln -s usr/lib "$root/lib"
readonly_bind() {
    mount --bind "$1" "$2"
    mount -o remount,bind,ro,nosuid,nodev "$2"
}
readonly_bind /mnt/lfs/usr "$root/usr"
readonly_bind /mnt/lfs/lib64 "$root/lib64"
# Font-dependent native tests use the installed system configuration. Expose only
# this declared nonsecret dependency, read-only, never the guest's general /etc.
if [[ -d /mnt/lfs/etc/fonts && ! -L /mnt/lfs/etc/fonts ]]; then
    mkdir "$root/etc/fonts"
    readonly_bind /mnt/lfs/etc/fonts "$root/etc/fonts"
fi
readonly_bind "$TODDY_INPUT" "$root/src"
# Browser-only private compiler tools: exact receipts, read-only payloads, no
# installed compiler replacement or broader filesystem exposure.
if [[ ( $TODDY_INPUT == /mnt/lfs/sources/phase2/inputs/firefox-153.2.0 &&
        $TODDY_WORK == /mnt/lfs/sources/phase2/work/firefox-build-1 ) ||
      ( $TODDY_INPUT == /mnt/lfs/sources/phase2/inputs/firefox-153.7.0 &&
        $TODDY_WORK == /mnt/lfs/sources/phase2/work/firefox-security-1537-1 ) ]]; then
    python3 /opt/toddy-build/scripts/build/phase2/browser_build_tools.py
    mkdir -p "$root/tools/wasi-sdk" "$root/tools/nasm"
    readonly_bind /mnt/lfs/sources/phase2/work/firefox-1/tools/wasi-sdk-25.0-x86_64-linux "$root/tools/wasi-sdk"
    readonly_bind /mnt/lfs/sources/phase2/work/nasm-1/stage "$root/tools/nasm"
fi
# This selected TLS consumer requires the qualified public factory CA policy.
# Expose only public anchors/certificates read-only, never SSL private/config
# directories or the guest's general /etc. CA generation uses its separate
# private-output profile below and cannot match this input identity.
if [[ "$TODDY_INPUT" == /mnt/lfs/sources/phase2/inputs/glib-networking-2.80.1 ||
      "$TODDY_INPUT" == /mnt/lfs/sources/phase2/inputs/libsoup-3.6.6 ||
      "$TODDY_INPUT" == /mnt/lfs/sources/phase2/inputs/evolution-data-server-3.60.2 ]]; then
    python3 - <<'PY'
import json
from pathlib import Path
r=json.loads(Path('/var/log/toddy/packages/ca-certificates_2026.11.09-1+toddy1_amd64.json').read_text())
assert r['installed']
assert len(list(Path('/mnt/lfs/etc/pki/anchors').glob('*.p11-kit')))==172
PY
    mkdir -p "$root/etc/pki/anchors" "$root/etc/ssl/certs"
    readonly_bind /mnt/lfs/etc/pki/anchors "$root/etc/pki/anchors"
    readonly_bind /mnt/lfs/etc/ssl/certs "$root/etc/ssl/certs"
    ln -s certs/ca-certificates.crt "$root/etc/ssl/cert.pem"
fi
# CA generation needs writable private trust paths at their real module names.
# These are aliases to this worker's outputs, never the installed /etc. Keep
# existing OpenSSL configuration/scripts mounted read-only from authenticated input.
if [[ ( $TODDY_INPUT == /mnt/lfs/sources/phase2/inputs/make-ca-data-1 && $TODDY_WORK == /mnt/lfs/sources/phase2/work/make-ca-data-1 ) || ( $TODDY_INPUT == /mnt/lfs/sources/phase2/inputs/make-ca-data-2 && $TODDY_WORK == /mnt/lfs/sources/phase2/work/make-ca-data-2 ) ]]; then
    python3 - "$TODDY_INPUT" "$TODDY_WORK" <<'CACHECK'
from pathlib import Path
import json,sys
source,work=map(Path,sys.argv[1:]);r=json.loads((source/'toddy-ca-data.json').read_text())
assert r['state']=='prepared' and r['source']==str(source) and r['work']==str(work)
for name,inode in r['candidate_inodes'].items():
 p=work/name;assert p.is_dir() and not p.is_symlink() and p.resolve().parent==work and p.stat().st_ino==inode
CACHECK
    mkdir -p "$root/etc/ssl" "$root/etc/pki"
    mount --bind "$TODDY_WORK/candidate-ssl" "$root/etc/ssl"
    mount --bind "$TODDY_WORK/candidate-pki" "$root/etc/pki"
    for config in openssl.cnf openssl.cnf.dist ct_log_list.cnf ct_log_list.cnf.dist misc private; do
        readonly_bind "$TODDY_INPUT/ssl-template/$config" "$root/etc/ssl/$config"
    done
fi
# One upstream Gcr test chmods this public encrypted sample before deriving its
# public key. Map only a byte-identical private worker copy; source stays RO.
if [[ $TODDY_INPUT == /mnt/lfs/sources/phase2/inputs/gcr-4.4.0.1 || $TODDY_INPUT == /mnt/lfs/sources/phase2/inputs/gcr-3.41.2 || $TODDY_INPUT == /mnt/lfs/sources/phase2/inputs/gcr-3.41.2-ssh-agent-1 ]]; then
    sample="$TODDY_INPUT/gcr/fixtures/pem-rsa-enc.key"
    expected=55b32dbd31618e5e949be919fb42ed7ca519f8e4ad5b352c9136ab7202e6ef4e
    [[ ! -L $sample && $(sha256sum "$sample" | cut -d' ' -f1) == "$expected" ]]
    fixture_dir="$TODDY_WORK/source-fixtures"
    [[ ! -L $fixture_dir ]]
    mkdir -p "$fixture_dir"
    [[ $(realpath -e "$fixture_dir") == "$fixture_dir" ]]
    fixture="$fixture_dir/pem-rsa-enc.key"
    if [[ ! -e $fixture && ! -L $fixture ]]; then
        install -m0600 -o "$TODDY_UID" -g "$TODDY_GID" "$sample" "$fixture"
    fi
    [[ -f $fixture && ! -L $fixture && $(sha256sum "$fixture" | cut -d' ' -f1) == "$expected" ]]
    mount --bind "$fixture" "$root/src/gcr/fixtures/pem-rsa-enc.key"
fi
# PAM's original unit drivers require the first-install deny policy. This is
# private to its synthetic read-only /etc, never a guest login configuration.
if [[ $TODDY_INPUT == /mnt/lfs/sources/phase2/inputs/linux-pam-1.7.2-security-1 ]]; then
    mkdir "$root/etc/pam.d"
    printf 'auth required /build/compile/modules/pam_deny/pam_deny.so\naccount required /build/compile/modules/pam_deny/pam_deny.so\npassword required /build/compile/modules/pam_deny/pam_deny.so\nsession required /build/compile/modules/pam_deny/pam_deny.so\n' > "$root/etc/pam.d/other"
fi
for name in ld.so.cache ld.so.conf; do
    if [[ -f /mnt/lfs/etc/$name ]]; then cp /mnt/lfs/etc/$name "$root/etc/$name"; fi
done
printf 'root:x:0:0:root:/root:/bin/false\ntester:x:%s:%s:builder:/build/home:/bin/bash\n' "$TODDY_UID" "$TODDY_GID" > "$root/etc/passwd"
printf 'root:x:0:\ntester:x:%s:\n' "$TODDY_GID" > "$root/etc/group"
printf 'passwd: files\ngroup: files\nhosts: files\n' > "$root/etc/nsswitch.conf"
printf '127.0.0.1 localhost\n::1 localhost\n' > "$root/etc/hosts"
# AccountsService and IBus original fixtures require a machine ID.
# Synthetic per-sandbox data only; never read/copy/change either real machine ID.
if [[ $TODDY_INPUT == /mnt/lfs/sources/phase2/inputs/accountsservice-26.27.3 ||
      $TODDY_INPUT == /mnt/lfs/sources/phase2/inputs/ibus-1.5.34 ]]; then
    printf '%s\n' 00000000000000000000000000000001 > "$root/etc/machine-id"
    chmod 0444 "$root/etc/machine-id"
fi
mount --bind "$TODDY_WORK" "$root/build"
# Exact disposable qualification fixture for metadata-only COW cache inputs.
# A plain parent bind intentionally omits child mounts; expose only this declared
# private overlay, never a general recursive bind or the builder's other mounts.
if [[ $TODDY_INPUT == /mnt/lfs/sources/phase2/inputs/kernel-overlay-test-1 &&
      $TODDY_WORK == /mnt/lfs/sources/phase2/work/kernel-overlay-test-1 ]]; then
    [[ $(findmnt -n -o FSTYPE --mountpoint "$TODDY_WORK/merged") == overlay ]]
    [[ $(stat -c %u "$TODDY_WORK/merged") == "$TODDY_UID" ]]
    mount --bind "$TODDY_WORK/merged" "$root/build/merged"
fi
# Exact real-kernel profile: only the private merged cache is writable. Hide
# upper/work/lower internals behind their root-only parent, and expose the
# immutable original independently at /src/cache for denial/source checks.
if [[ $TODDY_INPUT == /mnt/lfs/sources/phase2/inputs/linux-landlock-7.1.8 &&
      $TODDY_WORK == /mnt/lfs/sources/phase2/work/kernel-landlock-1 ]]; then
    [[ $(findmnt -n -o UUID --mountpoint "$TODDY_WORK") == c6c4176d-faed-4ee3-9ae0-94914a0af666 ]]
    [[ $(findmnt -n -o FSTYPE --mountpoint "$TODDY_WORK/merged") == overlay ]]
    [[ $(stat -c %u "$TODDY_WORK/merged") == "$TODDY_UID" ]]
    [[ $(stat -c %u:%a "$TODDY_WORK/private-overlay") == 0:700 ]]
    mount --bind "$TODDY_WORK/merged" "$root/build/merged"
    readonly_bind /mnt/lfs/sources/linux-7.1.8 "$root/src/cache"
    # Expose only the already-qualified original package and its provenance for
    # stage reuse, never the package database, full cache or signing material.
    if [[ -f "$TODDY_INPUT/toddy-foundation-kernel.deb" &&
          -f "$TODDY_INPUT/toddy-foundation-kernel.json" ]]; then
        readonly_bind /var/cache/toddy/packages/linux-kernel_7.1.8-1_amd64.deb "$root/src/toddy-foundation-kernel.deb"
        readonly_bind /var/log/toddy/packages/linux-kernel_7.1.8-1_amd64.json "$root/src/toddy-foundation-kernel.json"
    fi
fi
mkdir -p "$TODDY_WORK/stage" "$TODDY_WORK/home"
chown "$TODDY_UID:$TODDY_GID" "$TODDY_WORK/stage" "$TODDY_WORK/home"
mount --bind "$TODDY_WORK/stage" "$root/stage"
mount -t tmpfs -o size=1g,mode=1777,nosuid,nodev tmpfs "$root/tmp"
mount -t proc -o nosuid,nodev,noexec proc "$root/proc"
for name in null zero random urandom; do
    touch "$root/dev/$name"
    mount --bind "/dev/$name" "$root/dev/$name"
done
# VTE's real PTY consumer needs a private terminal allocator. Never bind the
# builder's /dev/pts or expose its existing terminals. Only this selected input
# receives a new devpts instance, allocated in this private mount namespace.
if [[ $TODDY_INPUT == /mnt/lfs/sources/phase2/inputs/vte-0.84.1 ]]; then
    mkdir "$root/dev/pts"
    mount -t devpts -o newinstance,nosuid,noexec,mode=0620,ptmxmode=0666,gid="$TODDY_GID" devpts "$root/dev/pts"
    ln -s pts/ptmx "$root/dev/ptmx"
fi
# Standard alias to this process's already exposed private proc descriptors.
ln -s /proc/self/fd "$root/dev/fd"
ln -s /proc/self/fd/0 "$root/dev/stdin"
ln -s /proc/self/fd/1 "$root/dev/stdout"
ln -s /proc/self/fd/2 "$root/dev/stderr"
# POSIX shared memory for native ORC/JIT/compiler tests. New tmpfs in this
# mount/IPC namespace only; never bind the guest/host shared-memory directory.
mkdir "$root/dev/shm"
mount -t tmpfs -o size=256m,mode=1777,nosuid,nodev tmpfs "$root/dev/shm"
# Read-only root covers the synthetic /etc and namespace topology, while the
# explicitly separate /build, /stage and /tmp mounts remain writable.
mount -o remount,ro "$root"
cd "$root/build"
ulimit -n 1024
ulimit -u 512
setpriv --no-new-privs --inh-caps=-all --ambient-caps=-all \
    --bounding-set=-all,+sys_chroot,+setuid,+setgid \
    chroot --userspec="$TODDY_UID:$TODDY_GID" --groups="$TODDY_GID" "$root" \
    /usr/bin/env -i HOME=/build/home PATH=/usr/bin:/usr/sbin LC_ALL=C.UTF-8 \
    CONFIG_SITE=/dev/null MAKEFLAGS=-j8 NINJAJOBS=8 "$@"
SANDBOX
