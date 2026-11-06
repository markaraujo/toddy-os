#!/bin/bash
# Prepared Toddy live /init. Installation/boot require the H09/H10 gates.
set -Eeuo pipefail
export PATH=/usr/bin:/usr/sbin LC_ALL=C HOME=/

if [[ $$ != 1 ]]; then
 printf 'Toddy live init must run as PID 1; no mounts attempted\n' >&2
 exit 1
fi

toddy_rescue() {
 local reason=$1
 trap - ERR
 set +e
 printf '\nTODDY_LIVE_ERROR: %s\n' "$reason" >&2
 printf 'Early boot stopped. A local recovery shell is available.\n' >&2
 printf 'Inspect mounts and diagnostics before rebooting.\n' >&2
 while :; do
  /bin/bash --noprofile --norc -i < /dev/console > /dev/console 2>&1
  sleep 1
 done
}
trap 'toddy_rescue "Command failed at line ${LINENO}, exit $?"' ERR

source /usr/lib/toddy/live_media.sh
IFS= read -r expected_id < /etc/toddy-live/media-id
IFS= read -r expected_sha < /etc/toddy-live/rootfs.sha256
if [[ ! $expected_id =~ ^[0-9a-f]{64}$ || ! $expected_sha =~ ^[0-9a-f]{64}$ ]]; then
 toddy_rescue 'Invalid embedded media identity or root digest'
fi

# Storage, filesystems and loop support are built into the selected kernel.
# No builder udev rules, module tree, firmware or account files are imported.
mount -t devtmpfs -o mode=0755,nosuid devtmpfs /dev
mount -t proc -o nosuid,nodev,noexec proc /proc
mount -t sysfs -o nosuid,nodev,noexec sysfs /sys
mount -t tmpfs -o mode=0755,nosuid,nodev,size=50% tmpfs /run

read -r -a command_line < /proc/cmdline
live_requested=0
for argument in "${command_line[@]}"; do
 case $argument in
  toddy.live) live_requested=1 ;;
  toddy.rescue) toddy_rescue 'Recovery requested on the kernel command line' ;;
  toddy.*) toddy_rescue 'Unsupported Toddy boot parameter' ;;
 esac
done
[[ $live_requested == 1 ]] || toddy_rescue 'Missing required toddy.live boot parameter'

mkdir -p /run/toddy/media /run/toddy/lower /run/toddy/upper /run/toddy/work
declare -A rejected_media=()
media_found=0
for ((attempt=1; attempt<=30; attempt++)); do
 # Device names originate from blkid and are constrained before mounting.
 # Read-only mounts plus embedded content checks decide acceptance, not names.
 candidates=$(blkid -c /dev/null -t TYPE=iso9660 -o device) || candidates=
 while IFS= read -r device; do
  [[ $device =~ ^/dev/[A-Za-z0-9._-]+$ && -b $device ]] || continue
  [[ ! ${rejected_media[$device]+present} ]] || continue
  if ! mount -t iso9660 -o ro,nosuid,nodev,noexec "$device" /run/toddy/media; then
   continue
  fi
  if toddy_verify_media /run/toddy/media "$expected_id" "$expected_sha"; then
   media_found=1
   break
  fi
  rejected_media[$device]=1
  umount /run/toddy/media
 done <<< "$candidates"
 [[ $media_found == 0 ]] || break
 sleep 1
done
[[ $media_found == 1 ]] || toddy_rescue 'No verified Toddy ISO filesystem found'
printf 'TODDY_LIVE_MEDIA_VERIFIED\n'

mount -t squashfs -o loop,ro,nodev /run/toddy/media/live/rootfs.squashfs /run/toddy/lower
mount -t overlay overlay \
 -o lowerdir=/run/toddy/lower,upperdir=/run/toddy/upper,workdir=/run/toddy/work,index=on \
 /newroot

# OverlayFS may downgrade unsupported indexing. Refuse that outcome because
# ACL copy-up would split hardlinks (ADR-0048), even if mount returned zero.
indexed_overlay=0
while read -r -a fields; do
 [[ ${fields[4]} == /newroot ]] || continue
 for ((index=6; index<${#fields[@]}; index++)); do
  if [[ ${fields[index]} == - && ${fields[index+1]} == overlay ]]; then
   super_options=,${fields[index+3]},
   [[ $super_options != *,index=on,* ]] || indexed_overlay=1
   break
  fi
 done
done < /proc/self/mountinfo
[[ $indexed_overlay == 1 ]] || toddy_rescue 'Required overlay hardlink indexing is unavailable'

[[ -f /newroot/usr/share/toddy/live-root.acl && ! -L /newroot/usr/share/toddy/live-root.acl ]] ||
 toddy_rescue 'Verified root is missing its ACL restoration data'
[[ -x /newroot/usr/bin/setfacl && -x /newroot/usr/lib/systemd/systemd ]] ||
 toddy_rescue 'Verified root is missing required native programs'

# The fixed metadata file is inside the hash-verified image. Physical restore
# runs in the new root before any Systemd service can observe stripped ACLs.
chroot /newroot /usr/bin/setfacl -P --restore=/usr/share/toddy/live-root.acl
# Runtime-only condition for the two live getty instances. Never put this file
# into the compressed root or an installed target (ADR-0058).
printf '%s\n' "$expected_id" > /run/toddy/live-session
printf 'TODDY_LIVE_ROOT_READY: writes are volatile\n'
# /run carries the media, lower and tmpfs upper mounts into the final root.
# Util-linux also moves /dev, /proc and /sys before executing the native init.
exec switch_root /newroot /usr/lib/systemd/systemd
