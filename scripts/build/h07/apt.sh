#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" apt_3.0.4.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/apt-inner.sh
conffiles=()
while IFS= read -r -d '' path; do
 conffiles+=(--conffile "/${path#"$LFS/sources/stage/apt/"}")
done < <(find "$LFS/sources/stage/apt/etc" -type f -print0)
python3 /opt/toddy-build/scripts/build/stage_package.py apt 3.0.4-1 \
 "$LFS/sources/stage/apt" --depends 'glibc (>= 2.44-1), gcc-runtime, dpkg, gnupg, berkeley-db, openssl, zlib, bzip2, xz, lz4, zstd, xxhash, systemd, libseccomp, ca-certificates' \
 --source apt_3.0.4.tar.xz "${conffiles[@]}" --recipe /opt/toddy-build/scripts/build/h07/apt.sh --install
