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
# One upstream Gcr test chmods this public encrypted sample before deriving its
# public key. Map only a byte-identical private worker copy; source stays RO.
if [[ $TODDY_INPUT == /mnt/lfs/sources/phase2/inputs/gcr-4.4.0.1 ]]; then
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
# AccountsService's original unprivileged daemon fixture requires a machine ID.
# Synthetic per-sandbox data only; never read/copy/change either real machine ID.
if [[ $TODDY_INPUT == /mnt/lfs/sources/phase2/inputs/accountsservice-26.27.3 ]]; then
    printf '%s\n' 00000000000000000000000000000001 > "$root/etc/machine-id"
    chmod 0444 "$root/etc/machine-id"
fi
mount --bind "$TODDY_WORK" "$root/build"
mkdir -p "$TODDY_WORK/stage" "$TODDY_WORK/home"
chown "$TODDY_UID:$TODDY_GID" "$TODDY_WORK/stage" "$TODDY_WORK/home"
mount --bind "$TODDY_WORK/stage" "$root/stage"
mount -t tmpfs -o size=1g,mode=1777,nosuid,nodev tmpfs "$root/tmp"
mount -t proc -o nosuid,nodev,noexec proc "$root/proc"
for name in null zero random urandom; do
    touch "$root/dev/$name"
    mount --bind "/dev/$name" "$root/dev/$name"
done
# Standard alias to this process's already exposed private proc descriptors.
ln -s /proc/self/fd "$root/dev/fd"
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
