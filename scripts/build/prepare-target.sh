#!/bin/bash
# LFS 13.1-systemd 2.4–2.7 and 4.2–4.4; only the designated guest disk.
set -euo pipefail
source "$(dirname "$0")/target.sh"
guard_guest
lsblk -o NAME,SIZE,TYPE,SERIAL,MOUNTPOINTS "$TARGET_DISK"
echo 'Plan: vdb GPT: 2 MiB BIOS boot, 512 MiB EFI, 8 GiB swap, remaining ext4 LFS.'
if [[ ${1:-} != --apply ]]; then
    echo 'Dry run: no disk, mount, user or filesystem changes.'
    exit 0
fi
[[ $(id -u) == 0 ]] || exit 1
if ! blkid "$TARGET_ROOT" >/dev/null 2>&1; then
    # Abort if anything is present; never wipe an unknown existing filesystem.
    [[ -z $(wipefs -n "$TARGET_DISK") ]] || { echo 'Nonblank target; refusing' >&2; exit 1; }
    [[ -z $(lsblk -nr -o MOUNTPOINTS "$TARGET_DISK" | tr -d '[:space:]') ]] || exit 1
    parted -s "$TARGET_DISK" mklabel gpt \
        mkpart bios 1MiB 3MiB set 1 bios_grub on \
        mkpart esp fat32 3MiB 515MiB set 2 esp on \
        mkpart swap linux-swap 515MiB 8707MiB \
        mkpart lfs ext4 8707MiB 100%
    partprobe "$TARGET_DISK"
    udevadm settle
    mkfs.fat -F 32 -n TODDY_ESP /dev/vdb2
    mkswap -L TODDY_SWAP /dev/vdb3
    mkfs.ext4 -L TODDY_LFS "$TARGET_ROOT"
fi
[[ $(blkid -s LABEL -o value "$TARGET_ROOT") == TODDY_LFS ]] || exit 1
install -d -m 755 "$LFS"
if ! mountpoint -q "$LFS"; then mount "$TARGET_ROOT" "$LFS"; fi
chown root:root "$LFS"
chmod 755 "$LFS"
guard_target
mkdir -p "$LFS"/{etc,var} "$LFS"/usr/{bin,lib,sbin} "$LFS"/{lib64,tools,sources}
chmod a+wt "$LFS/sources"
for item in bin lib sbin; do
    if [[ ! -e $LFS/$item ]]; then ln -s "usr/$item" "$LFS/$item"; fi
    [[ $(readlink "$LFS/$item") == usr/"$item" ]] || exit 1
done
getent group lfs >/dev/null || groupadd lfs
id lfs >/dev/null 2>&1 || useradd -s /bin/bash -g lfs -m -k /dev/null lfs
chown lfs "$LFS"/usr{,/*} "$LFS"/{var,etc,tools,lib64}
cat > /home/lfs/.bash_profile <<'PROFILE'
exec env -i HOME=$HOME TERM=${TERM:-dumb} PS1='\u:\w\$ ' /bin/bash
PROFILE
cat > /home/lfs/.bashrc <<'RC'
set +h
umask 022
LFS=/mnt/lfs
LC_ALL=POSIX
LFS_TGT=$(uname -m)-lfs-linux-gnu
PATH=/usr/bin
if [ ! -L /bin ]; then PATH=/bin:$PATH; fi
PATH=$LFS/tools/bin:$PATH
CONFIG_SITE=$LFS/usr/share/config.site
MAKEFLAGS=-j8
export LFS LC_ALL LFS_TGT PATH CONFIG_SITE MAKEFLAGS
RC
chown lfs:lfs /home/lfs/.bash{rc,_profile}
# Only disable the optional global bashrc in this disposable builder, per 4.4.
if [[ -f /etc/bash.bashrc ]]; then mv /etc/bash.bashrc /etc/bash.bashrc.NOUSE; fi
root_uuid=$(blkid -s UUID -o value "$TARGET_ROOT")
if ! grep -q ' /mnt/lfs ' /etc/fstab; then
    echo "UUID=$root_uuid /mnt/lfs ext4 defaults,nofail 0 2" >> /etc/fstab
fi
swapon /dev/vdb3 || [[ $(swapon --show=NAME --noheadings) == /dev/vdb3 ]]
lsblk -o NAME,SIZE,TYPE,SERIAL,FSTYPE,LABEL,MOUNTPOINTS
findmnt "$LFS"
echo 'Target preparation postconditions passed.'
