#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,shutil,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','gcr3'],text=True,env=env)=='install ok installed 3.41.2-1+toddy1'
for pc in ['gcr-base-3','gcr-3','gcr-ui-3','gck-1']:assert subprocess.check_output(prefix+['pkg-config','--modversion',pc],text=True,env=env).strip()=='3.41.2'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
work=Path('/mnt/lfs/sources/phase2/work/gcr3-patched-1');expected=json.loads((work/'stage-results.json').read_text())['consumer']
with tempfile.TemporaryDirectory(prefix='toddy-gcr3-',dir='/mnt/lfs/tmp') as directory:
 p=Path(directory);shutil.copyfile(work/'native-probe',p/'probe');(p/'probe').chmod(0o755)
 assert hashlib.sha256((p/'probe').read_bytes()).digest()==hashlib.sha256((work/'native-probe').read_bytes()).digest() and not Path('/mnt/lfs/stage').exists()
 r=subprocess.run(prefix+['/tmp/'+p.name+'/probe'],env=env,capture_output=True,text=True,timeout=20,check=True);consumer=json.loads(r.stdout)
assert consumer==expected
old=json.loads(Path('/var/log/toddy/packages/gcr_4.4.0.1-1+toddy1_amd64.json').read_text());assert old['installed']
with Path('/var/cache/toddy/packages/gcr_4.4.0.1-1+toddy1_amd64.deb').open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==old['archive_sha256']
for name,row in old['payload'].items():
 p=Path('/mnt/lfs')/name.lstrip('/');st=p.lstat();assert (st.st_mode,st.st_uid,st.st_gid)==(row['mode'],row['uid'],row['gid'])
 if 'sha256' in row:
  with p.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256']
 elif 'symlink' in row:assert p.is_symlink() and os.readlink(p)==row['symlink']
 else:assert row['directory'] and p.is_dir()
Path('/var/log/toddy/phase2/gcr3-installed-consumer.json').write_text(json.dumps({'scope':'Installed Gcr3 C transport/refusal/recovery/SDK/audit and co-installation only; native GTK3 UI/keyring/PAM acceptance pending','consumer':consumer,'Gcr4_payload_entries_unchanged':len(old['payload']),'Gcr4_archive_unchanged':True,'legacy_GI_and_SSH_agent':'Not built/enabled','shared_schema_cache':'New PGP schema union pending before actual native UI'},indent=2)+'\n')
PY
