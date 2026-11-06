#!/bin/bash
# Runs ONLY inside the disposable build VM, never on the workstation.
set -euo pipefail
[[ $(hostname) == toddy-builder ]] || { echo 'Wrong target hostname' >&2; exit 1; }
[[ $(systemd-detect-virt) == kvm || $(systemd-detect-virt) == qemu ]] || exit 1
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y build-essential bison gawk texinfo python3 wget curl ca-certificates \
    xz-utils patch m4 file rsync git parted e2fsprogs dosfstools gdisk \
    bc flex libssl-dev libelf-dev pkg-config zstd unzip acl attr
# LFS 13.1-systemd section 2.2 requires these links, in this guest only.
ln -sfn bash /bin/sh
update-alternatives --set awk /usr/bin/gawk
update-alternatives --set yacc /usr/bin/bison.yacc
install -d -m 755 /var/log/toddy
LC_ALL=C dpkg-query -W > /var/log/toddy/builder-packages.tsv
