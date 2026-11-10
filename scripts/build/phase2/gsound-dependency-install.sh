#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
root=Path('/opt/toddy-build');T=Path('/mnt/lfs');l=Path('/var/log/toddy')
sys.path.insert(0,str(root/'scripts/build/phase2'));from qualify_gsound import qualify,digest
proof=qualify(root)
old=json.loads((l/'build/b02-gsound-install.failed.json').read_text());assert old['recipe_exit']==1 and old['postcheck_exit'] is None and old['changed_paths']==22
assert 'Version of libcanberra on system is 0.30-1+toddy2' in (l/'build/b02-gsound-install.log').read_text()
assert subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Status} ${Version}','gsound'],text=True)=='install ok unpacked 1.0.3-1+toddy1'
assert subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Status} ${Version}','libcanberra'],text=True)=='install ok installed 0.30-1+toddy2'
archive=Path('/var/cache/toddy/packages/gsound_1.0.3-1+toddy1_amd64.deb')
assert digest(archive)=='9cc4d3f270e96549440e6bd27c72d07700d583ec1adbbbd1ac3636d8d25fc2ee'
record=json.loads((l/'packages/gsound_1.0.3-1+toddy1_amd64.json').read_text());assert not record['installed']
for relative,sha in proof['stage_sha256'].items():assert digest(T/relative)==sha
for relative,row in record['payload'].items():
 if 'sha256' in row:assert digest(T/relative.lstrip('/'))==row['sha256']
source=T/'sources/stage/phase2-gsound';destination=T/'sources/stage/phase2-gsound-dependency-2'
assert not destination.exists() and set(p.name for p in (source/'DEBIAN').iterdir())=={'control'}
size=sum(p.stat().st_size for p in source.rglob('*') if p.is_file() and not p.is_symlink())
s=os.statvfs(T);assert s.f_bavail*s.f_frsize>=16*1024**3+3*size+8*1024**2
shutil.copytree(source,destination,symlinks=True,ignore=shutil.ignore_patterns('DEBIAN'))
for p in source.rglob('*'):
 if p.is_file() and not p.is_symlink() and 'DEBIAN' not in p.relative_to(source).parts:assert digest(p)==digest(destination/p.relative_to(source))
subprocess.run(['python3',str(root/'scripts/build/stage_package.py'),'gsound','1.0.3-1+toddy2',str(destination),'--source','gsound-1.0.3.tar.xz','--recipe','scripts/build/phase2/gsound-dependency-install.sh','--depends','glibc (>= 2.44-1+toddy1), glib (= 2.88.3-1+toddy2), libcanberra (= 0.30-1+toddy2)','--install'],cwd=root,check=True)
for relative,sha in proof['stage_sha256'].items():assert digest(T/relative)==sha
assert digest(archive)=='9cc4d3f270e96549440e6bd27c72d07700d583ec1adbbbd1ac3636d8d25fc2ee'
PY
