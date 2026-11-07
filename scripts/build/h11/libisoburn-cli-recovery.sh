#!/bin/bash
# Preserve the already tested native binaries; correct only the optional profile.
source /opt/toddy-build/scripts/build/h06/common.sh
python3 /opt/toddy-build/scripts/build/h10/require_media_tools.py
python3 "$SOURCE_TOOL" --verify-only libisoburn-1.5.8.pl02.tar.gz
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil,subprocess
root=Path('/mnt/lfs')
record_path=Path('/var/log/toddy/packages/libisoburn_1.5.8.pl02-1_amd64.json')
record=json.loads(record_path.read_text())
assert record['installed'] and record['version']=='1.5.8.pl02-1'
assert subprocess.check_output(['chroot',str(root),'dpkg-query','-W','-f=${Status} ${Version}','libisoburn'],text=True)=='install ok installed 1.5.8.pl02-1'
archive=Path('/var/cache/toddy/packages/libisoburn_1.5.8.pl02-1_amd64.deb')
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(archive)==record['archive_sha256']
for name,row in record['payload'].items():
    path=root/name.lstrip('/');info=path.lstat()
    assert (info.st_mode,info.st_uid,info.st_gid)==(row['mode'],row['uid'],row['gid']),name
    if 'sha256' in row:assert not path.is_symlink() and digest(path)==row['sha256'],name
    elif 'symlink' in row:assert path.is_symlink() and str(path.readlink())==row['symlink'],name
stage=root/'sources/stage/libisoburn-cli-recovery'
assert not stage.exists() and not stage.is_symlink()
evidence=root/'sources/evidence/h11-libisoburn-cli';evidence.mkdir(mode=0o700)
accepted=evidence/'accepted.deb';shutil.copyfile(archive,accepted)
assert digest(accepted)==record['archive_sha256']
data=evidence/'accepted-payload.tar'
with data.open('xb') as output:subprocess.run(['chroot',str(root),'/usr/bin/dpkg-deb','--fsys-tarfile','/'+str(accepted.relative_to(root))],stdout=output,check=True)
stage.mkdir()
subprocess.run(['chroot',str(root),'/usr/bin/tar','--extract','--numeric-owner','--same-permissions',
    '--file=/'+str(data.relative_to(root)),'--directory=/'+str(stage.relative_to(root))],check=True)
(evidence/'xorriso-tcltk.info').write_bytes((stage/'usr/share/info/xorriso-tcltk.info').read_bytes())
(evidence/'predecessor.json').write_text(json.dumps({'archive_sha256':record['archive_sha256'],
    'record_sha256':digest(record_path),'payload':record['payload']},indent=2)+'\n')
PY
python3 /opt/toddy-build/scripts/build/h11/libisoburn-cli-stage.py "$LFS/sources/stage/libisoburn-cli-recovery"
python3 /opt/toddy-build/scripts/build/stage_package.py libisoburn 1.5.8.pl02-2 \
 "$LFS/sources/stage/libisoburn-cli-recovery" --depends 'glibc, libburn, libisofs, acl, zlib, readline, ncurses, bash, coreutils, grep, sed, gawk, util-linux' \
 --source libisoburn-1.5.8.pl02.tar.gz --recipe /opt/toddy-build/scripts/build/h11/libisoburn-cli-recovery.sh --install
chroot_run <<'INNER'
set -euo pipefail
install-info --delete /sources/evidence/h11-libisoburn-cli/xorriso-tcltk.info /usr/share/info/dir
INNER
