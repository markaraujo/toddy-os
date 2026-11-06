#!/bin/bash
set -euo pipefail
[[ $(id -un) == lfs && $LFS == /mnt/lfs && $LFS_TGT == x86_64-lfs-linux-gnu ]] || exit 1
[[ $(findmnt -n -o SOURCE --mountpoint "$LFS") == /dev/vdb4 ]] || exit 1
SOURCE_TOOL=/opt/toddy-build/scripts/build/source.py
cd "$LFS/sources"
unpack() { python3 "$SOURCE_TOOL" "$1"; }
verify() { python3 "$SOURCE_TOOL" --verify-only "$1"; }
mkdir -p "$LFS/sources/evidence"
