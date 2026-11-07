#!/bin/bash
# Preserve the already installed native build; verify bytes and retry postchecks.
source /opt/toddy-build/scripts/build/h06/common.sh
python3 "$SOURCE_TOOL" --verify-only apt_3.0.4.tar.xz
python3 - <<'PY'
from datetime import datetime, timezone
import hashlib,json,shutil,stat,subprocess
from pathlib import Path
root=Path('/mnt/lfs')
record_path=Path('/var/log/toddy/packages/apt_3.0.4-1_amd64.json')
record=json.loads(record_path.read_text())
assert record['installed'] and record['packaging_backend']['kind']=='source-built-native-dpkg'
assert subprocess.check_output(['chroot',str(root),'dpkg-query','-W','-f=${Status} ${Version}','apt'],text=True)=='install ok installed 3.0.4-1'
def sha(path):
 with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
assert sha(Path('/var/cache/toddy/packages/apt_3.0.4-1_amd64.deb'))==record['archive_sha256']
for virtual,row in record['payload'].items():
 if row.get('directory'):continue
 path=root/virtual.lstrip('/')
 if 'symlink' in row:assert path.is_symlink() and path.readlink().as_posix()==row['symlink'],virtual
 else:assert not path.is_symlink() and sha(path)==row['sha256'],virtual
 info=path.lstat()
 assert (stat.S_IMODE(info.st_mode),info.st_uid,info.st_gid)==(stat.S_IMODE(row['mode']),row['uid'],row['gid']),virtual
base=root/'sources/evidence/h07-apt'
backup=base/'retries'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
backup.mkdir(parents=True)
for name in ('native-repository.log','https-worker.json','ctest.log','native-cache.log','native-cache-result.json'):
 if (base/name).is_file():shutil.copyfile(base/name,backup/name)
(backup/'installed-revalidation.json').write_text(json.dumps({'archive_sha256':record['archive_sha256'],
 'component_sha256':sha(record_path),'payload_reverified':True,'installed':True},indent=2)+'\n')
print('Existing native APT archive and entire installed payload verified; previous reports preserved')
PY
chroot_run <<'INNER'
set -euo pipefail
cd /sources/apt-3.0.4/build
su tester -c 'ctest --output-on-failure --no-tests=error' 2>&1 | tee /sources/evidence/h07-apt/ctest.log
INNER
