#!/bin/bash
# Preserve LFS 6.2 cross settings; native Glibc patch 49 reverts their premise.
source /opt/toddy-build/scripts/build/h06/common.sh
python3 - <<'PY'
from pathlib import Path
import hashlib,json
target=Path('/mnt/lfs')
site=target/'usr/share/config.site'
expected=b'ac_cv_func_posix_spawn_file_actions_addchdir=yes\nac_cv_func_posix_spawn_file_actions_addfchdir=yes\n'
assert not site.is_symlink() and site.read_bytes()==expected,'Preserve changed config.site for review'
record=Path('/var/log/toddy/packages/lfs-build-support_13.1-1_all.json')
if record.exists():
 row=json.loads(record.read_text());assert row['installed']
 with Path('/var/cache/toddy/packages/lfs-build-support_13.1-1_all.deb').open('rb') as stream:
  assert hashlib.file_digest(stream,'sha256').hexdigest()==row['archive_sha256']
 assert hashlib.sha256(expected).hexdigest()==row['payload']['/usr/share/config.site']['sha256']
print('Original book cross settings verified; predecessor archive preserved when installed')
PY
stage="$LFS/sources/stage/lfs-build-support-native"
[[ ! -e "$stage" ]]
mkdir -p "$stage/usr/share/doc/lfs-build-support"
cp "$LFS/usr/share/config.site" "$stage/usr/share/doc/lfs-build-support/config.site.book-cross-original"
cat > "$stage/usr/share/config.site" <<'SITE'
# Native builds detect capabilities directly; no forced feature-cache answers.
# Glibc 2.44 upstream_fixes-3 patch 49 reverts the POSIX spawn header aliases.
# Original LFS 13.1 cross settings are retained in this package's documentation.
SITE
cp /opt/toddy-build/LICENSES/LFS-MIT.txt "$stage/usr/share/doc/lfs-build-support/copyright"
cp /opt/toddy-build/config/books.lock.json "$stage/usr/share/doc/lfs-build-support/book-sources.json"
python3 /opt/toddy-build/scripts/build/stage_package.py lfs-build-support 13.1-2 \
 "$stage" --architecture all --depends 'glibc, bash' \
 --recipe /opt/toddy-build/scripts/build/h07/lfs-build-support.sh --install
