#!/bin/bash
# Fixed builder/native jobs in one private protected-stage/source namespace.
set -euo pipefail
[[ $(id -u) == 0 && $# == 1 ]]
case $1 in
    base|live|qualify-base|qualify-live|finalize-base|finalize-live|stage-live|media-compress|media-initramfs|media-iso|mvp-base|mvp-live|qualify-mvp-base|qualify-mvp-live|finalize-mvp-base|finalize-mvp-live|stage-mvp-live|media-mvp-compress|media-mvp-initramfs|media-mvp-iso|media-mvp-installer-compress|media-mvp-installer-initramfs|media-mvp-installer-iso) ;;
    seal-mvp-installer|embed-mvp-installer|signatures-export3|signatures-export3-reconcile2|signatures-export4) ;;
    inputs-base-requirements|inputs-live-requirements|inputs-base-prepare|inputs-live-prepare|inputs-mvp-base-requirements|inputs-mvp-live-requirements|inputs-mvp-base-prepare|inputs-mvp-live-prepare) ;;
    custody-h10-expanded-inspect|custody-h10-expanded-export|custody-h10-expanded-receipt|custody-h10-expanded-metadata|custody-h10-expanded-retire|custody-h11-expanded-inspect|custody-h11-expanded-export|custody-h11-expanded-receipt|custody-h11-expanded-metadata|custody-h11-expanded-retire|custody-mvp-offline-inspect|custody-mvp-offline-export|custody-mvp-offline-receipt|custody-mvp-offline-metadata|custody-mvp-offline-retire|custody-mvp-live-inspect|custody-mvp-live-export|custody-mvp-live-receipt|custody-mvp-live-metadata|custody-mvp-live-retire|custody-offline-inspect|custody-offline-export|custody-offline-receipt|custody-offline-metadata|custody-offline-retire|custody-live-inspect|custody-live-export|custody-live-receipt|custody-live-metadata|custody-live-retire) ;;
    *) exit 2 ;;
esac
source /opt/toddy-build/scripts/build/target.sh
guard_target
exec 9>/var/log/toddy/build/build.lock
flock -n 9
[[ ! -e /var/log/toddy/build/input-sync.running ]]
shopt -s nullglob
running=(/var/log/toddy/build/*.running.json)
[[ ${#running[@]} == 0 ]]
# isolated.sh holds this lock during compilation. Cover its dispatch interval too.
/usr/bin/python3 -I -c 'import sys;sys.path.insert(0,"/opt/toddy-build/scripts/build/phase2");from image_assemble import unclosed_compiler_jobs;jobs=unclosed_compiler_jobs("/var/log/toddy/phase2");assert not jobs,"Reconcile unclosed compiler jobs: "+repr(jobs)'
[[ -b /mnt/lfs/dev/vdb4 && -d /mnt/lfs/proc/self && -d /mnt/lfs/sys/dev/block && -d /mnt/lfs/run ]]
# The shell heredoc replaces stdin. Preserve only the original bounded receipt
# channel for fixed custody actions, never as shell source or command arguments.
exec 8<&0
exec /usr/bin/unshare --mount --propagation private /usr/bin/env -i PATH=/usr/bin:/usr/sbin HOME=/root LC_ALL=C /usr/bin/bash --noprofile --norc -s -- "$1" <<'NAMESPACE'
set -euo pipefail
lock=/var/log/toddy/build/build.lock
[[ $(readlink -f "$lock") == "$lock" && $(readlink /proc/self/fd/9) == "$lock" ]]
[[ $(stat -Lc '%d:%i' /proc/self/fd/9) == $(stat -c '%d:%i' "$lock") ]]
grep -Eq '^lock:.*FLOCK.*WRITE' /proc/self/fdinfo/9
source /opt/toddy-build/scripts/build/target.sh
guard_target
[[ $(readlink /proc/self/ns/mnt) != $(readlink /proc/1/ns/mnt) ]]
source=/opt/toddy-build
binding=/mnt/lfs/opt/toddy-build
sources=/mnt/lfs/sources
stage=$sources/stage
[[ $(readlink -f "$source") == "$source" && $(stat -c '%u:%g' "$source") == 0:0 ]]
mode=$(stat -c %a "$source"); (( (8#$mode & 0022) == 0 ))
[[ -d /mnt/lfs/opt && ! -L /mnt/lfs/opt && ! -e $binding && ! -L $binding ]]
[[ -d $sources && ! -L $sources && $(readlink -f "$sources") == "$sources" ]]
[[ -d $stage && ! -L $stage && $(readlink -f "$stage") == "$stage" && $(stat -c '%u:%g' "$stage") == 0:0 ]]
mode=$(stat -c %a "$stage"); (( (8#$mode & 0022) == 0 ))
[[ $(stat -c %d "$stage") == $(stat -c %d /mnt/lfs) ]]
legacy_pin=$(stat -c '%d:%i:%u:%g:%a' "$sources")
stage_pin=$(stat -c '%d:%i:%u:%g:%a' "$stage")
[[ -d /run && ! -L /run && $(stat -c '%u:%g' /run) == 0:0 ]]
anchor=$(mktemp -d /run/toddy-image-stage-anchor.XXXXXX)
[[ $anchor == /run/toddy-image-stage-anchor.* && $(readlink -f "$anchor") == "$anchor" && $(stat -c '%u:%g:%a' "$anchor") == 0:0:700 ]]
anchor_pin=$(stat -c '%d:%i' "$anchor")
anchor_mounted=0; sources_mounted=0; stage_mounted=0; binding_created=0; source_mounted=0; placeholder_created=0
cleanup() {
    code=$?
    # Never lazy-unmount, recurse through real stage, or remove a persisted tree.
    if (( source_mounted )); then /usr/bin/umount "$binding" || exit 1; fi
    if (( binding_created )); then
        [[ $(stat -c '%d:%i' "$binding") == "$binding_pin" ]] || exit 1
        rmdir "$binding" || exit 1
    fi
    if (( stage_mounted )); then /usr/bin/umount "$stage" || exit 1; fi
    if (( placeholder_created )); then
        [[ $sources_mounted == 1 && $(stat -c '%d:%i' "$stage") == "$placeholder_pin" ]] || exit 1
        rmdir "$stage" || exit 1
    fi
    if (( sources_mounted )); then
        /usr/bin/umount "$sources" || exit 1
        [[ $(stat -c '%d:%i:%u:%g:%a' "$sources") == "$legacy_pin" ]] || exit 1
        [[ $(stat -c '%d:%i:%u:%g:%a' "$stage") == "$stage_pin" ]] || exit 1
    fi
    if (( anchor_mounted )); then /usr/bin/umount "$anchor" || exit 1; fi
    [[ $(stat -c '%d:%i' "$anchor") == "$anchor_pin" ]] || exit 1
    rmdir "$anchor" || exit 1
    exit "$code"
}
trap cleanup EXIT
# Pin the real protected stage BEFORE hiding its group-writable legacy parent.
/usr/bin/mount --bind "$stage" "$anchor"
anchor_mounted=1
/usr/bin/mount -o remount,bind,rw,exec,nosuid,nodev "$anchor"
[[ $(stat -c '%d:%i:%u:%g:%a' "$anchor") == "$stage_pin" ]]
/usr/bin/mount -t tmpfs -o size=1m,mode=0755,nosuid,nodev,noexec toddy-image-sources "$sources"
sources_mounted=1
[[ $(stat -c '%u:%g:%a' "$sources") == 0:0:755 ]]
[[ $(/usr/bin/findmnt -rn -o FSTYPE --mountpoint "$sources") == tmpfs ]]
mkdir -m 0755 "$stage"
placeholder_created=1; placeholder_pin=$(stat -c '%d:%i' "$stage")
/usr/bin/mount --bind "$anchor" "$stage"
stage_mounted=1
/usr/bin/mount -o remount,bind,rw,exec,nosuid,nodev "$stage"
[[ $(stat -c '%d:%i:%u:%g:%a' "$stage") == "$stage_pin" ]]
options=$(/usr/bin/findmnt -rn -o OPTIONS --mountpoint "$stage")
for flag in rw nosuid nodev; do [[ ,$options, == *,$flag,* ]]; done
[[ ,$options, != *,noexec,* ]]
mkdir -m 0755 "$binding"
binding_created=1; binding_pin=$(stat -c '%d:%i' "$binding")
/usr/bin/mount --bind "$source" "$binding"
source_mounted=1
/usr/bin/mount -o remount,bind,ro,nosuid,nodev,noexec "$binding"
options=$(/usr/bin/findmnt -rn -o OPTIONS --mountpoint "$binding")
for flag in ro nosuid nodev noexec; do [[ ,$options, == *,$flag,* ]]; done
[[ $(stat -c '%d:%i' "$source") == $(stat -c '%d:%i' "$binding") ]]
case $1 in
    custody-h10-expanded-*|custody-h11-expanded-*|custody-mvp-offline-*|custody-mvp-live-*)
        action=${1##*-}; profile=${1#custody-}; profile=${profile%-*}
        /usr/bin/env -i PATH=/usr/bin:/usr/sbin HOME=/root LC_ALL=C /usr/bin/python3 -I /opt/toddy-build/scripts/build/phase2/candidate_root_custody.py "$profile" "$action" <&8 8<&- ;;
    custody-offline-*)
        action=${1#custody-offline-}
        /usr/bin/env -i PATH=/usr/bin:/usr/sbin HOME=/root LC_ALL=C /usr/bin/python3 -I /opt/toddy-build/scripts/build/phase2/candidate_root_custody.py "$action" <&8 8<&- ;;
    custody-live-*)
        action=${1#custody-live-}
        /usr/bin/env -i PATH=/usr/bin:/usr/sbin HOME=/root LC_ALL=C /usr/bin/python3 -I /opt/toddy-build/scripts/build/phase2/candidate_root_custody.py live "$action" <&8 8<&- ;;
    inputs-base-requirements|inputs-live-requirements|inputs-base-prepare|inputs-live-prepare|inputs-mvp-base-requirements|inputs-mvp-live-requirements|inputs-mvp-base-prepare|inputs-mvp-live-prepare)
        action=${1#inputs-}; kind=${action%-*}; operation=${action##*-}
        /usr/bin/env -i PATH=/usr/bin:/usr/sbin HOME=/root LC_ALL=C /usr/bin/python3 -I /opt/toddy-build/scripts/build/phase2/image_inputs.py "$operation" "$kind" 8<&- ;;
    signatures-export4)
        /usr/bin/env -i PATH=/usr/bin:/usr/sbin HOME=/root LC_ALL=C /usr/bin/python3 -I /opt/toddy-build/scripts/build/phase2/export4_public_signatures.py <&8 8<&- ;;
    signatures-export3-reconcile2)
        /usr/bin/env -i PATH=/usr/bin:/usr/sbin HOME=/root LC_ALL=C /usr/bin/python3 -I /opt/toddy-build/scripts/build/phase2/export3_public_signatures_reconcile2.py <&8 8<&- ;;
    signatures-export3)
        /usr/bin/env -i PATH=/usr/bin:/usr/sbin HOME=/root LC_ALL=C /usr/bin/python3 -I /opt/toddy-build/scripts/build/phase2/export3_public_signatures.py <&8 8<&- ;;
    seal-mvp-installer|embed-mvp-installer)
        operation=${1%%-*}
        /usr/sbin/chroot /mnt/lfs /usr/bin/env -i PATH=/usr/bin:/usr/sbin HOME=/root LC_ALL=C /usr/bin/python3 -I /opt/toddy-build/scripts/build/phase2/image_installer.py "$operation" 8<&- ;;
    media-compress|media-initramfs|media-iso|media-mvp-compress|media-mvp-initramfs|media-mvp-iso|media-mvp-installer-compress|media-mvp-installer-initramfs|media-mvp-installer-iso)
        # Media coordinator owns TARGET=/mnt/lfs and invokes native tools itself.
        # Keep it builder-side in this protected view with the SAME lease FD9.
        action=${1#media-}
        /usr/bin/env -i PATH=/usr/bin:/usr/sbin HOME=/root LC_ALL=C /usr/bin/python3 -I /opt/toddy-build/scripts/build/phase2/image_media.py "$action" 8<&- ;;
    *)
        # Ubuntu's chroot is /usr/sbin; all following programs are native.
        /usr/sbin/chroot /mnt/lfs /usr/bin/env -i PATH=/usr/bin:/usr/sbin HOME=/root LC_ALL=C \
            /usr/bin/python3 -I /opt/toddy-build/scripts/build/phase2/image_assemble.py "$1" 8<&- ;;
esac
NAMESPACE
