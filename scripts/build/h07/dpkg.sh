#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" dpkg_1.22.22.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/dpkg-inner.sh
conffiles=()
if [[ -d "$LFS/sources/stage/dpkg/etc" ]]; then
 while IFS= read -r -d '' path; do
  conffiles+=(--conffile "/${path#"$LFS/sources/stage/dpkg/"}")
 done < <(find "$LFS/sources/stage/dpkg/etc" -type f -print0)
fi
python3 /opt/toddy-build/scripts/build/stage_package.py dpkg 1.22.22-1 \
 "$LFS/sources/stage/dpkg" --depends 'glibc (>= 2.44-1), gcc-runtime, libmd, zlib, bzip2, xz, zstd, ncurses, perl, tar, coreutils' \
 --source dpkg_1.22.22.tar.xz "${conffiles[@]}" \
 --recipe /opt/toddy-build/scripts/build/h07/dpkg.sh --install
