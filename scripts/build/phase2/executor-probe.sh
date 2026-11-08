#!/bin/bash
# Guest-only native root/UID IPC fixture in a disposable synthetic root.
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
[[ $(id -u) == 0 && $# == 2 ]] || exit 64
input=$(realpath -e -- "$1"); work=$(realpath -e -- "$2")
[[ $input == "$1" && $work == "$2" && $(dirname "$input") == /mnt/lfs/sources/phase2/inputs && $(dirname "$work") == /mnt/lfs/sources/phase2/work ]] || exit 65
[[ $(stat -c %u "$input") == 0 && $(stat -c %u "$work") == 0 ]] || exit 65
exec 9>/var/log/toddy/build/build.lock
flock -n -E 75 9
if compgen -G '/var/log/toddy/build/*.running.json' >/dev/null; then exit 75; fi
root=$(mktemp -d /run/toddy-executor-probe.XXXXXX)
trap 'rmdir "$root"' EXIT
export TODDY_ROOT_PROBE=$root TODDY_PROBE_INPUT=$input TODDY_PROBE_WORK=$work
unshare --mount --pid --net --ipc --fork /bin/bash -s <<'NAMESPACE'
set -euo pipefail
exec 9>&-
[[ $$ == 1 ]] || exit 70
mount --make-rprivate /
root=$TODDY_ROOT_PROBE
mount -t tmpfs -o size=32m,nosuid,nodev tmpfs "$root"
mkdir -p "$root"/{usr,etc,lib64,src,build,tmp,proc,dev,run,var/lib}
ln -s usr/bin "$root/bin";ln -s usr/sbin "$root/sbin";ln -s usr/lib "$root/lib"
for pair in "/mnt/lfs/usr:$root/usr" "/mnt/lfs/lib64:$root/lib64" "$TODDY_PROBE_INPUT:$root/src";do
    source=${pair%%:*};dest=${pair#*:}
    mount --bind "$source" "$dest";mount -o remount,bind,ro,nosuid,nodev "$dest"
done
mount --bind "$TODDY_PROBE_WORK" "$root/build"
for name in ld.so.cache ld.so.conf;do [[ ! -f /mnt/lfs/etc/$name ]] || cp /mnt/lfs/etc/$name "$root/etc/$name";done
printf 'root:x:0:0:root:/root:/bin/false\ntester:x:101:101:tester:/build/client:/bin/false\nnobody:x:65534:65534:nobody:/:/bin/false\n_apt:x:42:42:apt:/:/bin/false\n' > "$root/etc/passwd"
printf 'root:x:0:\ntester:x:101:\nnogroup:x:65534:\n_apt:x:42:\n' > "$root/etc/group"
printf 'passwd: files\ngroup: files\nhosts: files\n' > "$root/etc/nsswitch.conf"
printf '127.0.0.1 localhost\n' > "$root/etc/hosts"
printf '0123456789abcdef0123456789abcdef\n' > "$root/etc/machine-id"
mount -t tmpfs -o size=64m,nosuid,nodev tmpfs "$root/tmp";chmod 1777 "$root/tmp"
mount -t proc -o nosuid,nodev,noexec proc "$root/proc"
for name in null zero random urandom;do touch "$root/dev/$name";mount --bind "/dev/$name" "$root/dev/$name";done
ln -s /proc/self/fd "$root/dev/fd"
# Namespace init becomes the chrooted native probe: /proc/1/root cannot expose
# the outer VM. Drop mount/chroot/ptrace/device capabilities before root tests.
exec chroot "$root" /usr/bin/env -i PATH=/usr/sbin:/usr/bin HOME=/root LANG=C.UTF-8 \
  /usr/bin/python3 /src/runtime/executor/native_probe.py
NAMESPACE
