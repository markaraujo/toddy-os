#!/bin/bash
# Frozen LFS 13.1 section 6.2 config.site; development support, not host data.
source /opt/toddy-build/scripts/build/h06/common.sh
stage="$LFS/sources/stage/lfs-build-support"
[[ ! -e "$stage" ]]
mkdir -p "$stage/usr/share/doc/lfs-build-support"
cat > "$stage/usr/share/config.site" <<'SITE'
ac_cv_func_posix_spawn_file_actions_addchdir=yes
ac_cv_func_posix_spawn_file_actions_addfchdir=yes
SITE
cmp "$stage/usr/share/config.site" "$LFS/usr/share/config.site"
cp /opt/toddy-build/LICENSES/LFS-MIT.txt "$stage/usr/share/doc/lfs-build-support/copyright"
cp /opt/toddy-build/config/books.lock.json "$stage/usr/share/doc/lfs-build-support/book-sources.json"
python3 /opt/toddy-build/scripts/build/stage_package.py lfs-build-support 13.1-1 \
 "$stage" --architecture all --depends 'glibc, bash' \
 --recipe /opt/toddy-build/scripts/build/h07/lfs-build-support.sh --install
