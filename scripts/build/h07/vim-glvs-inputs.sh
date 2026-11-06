#!/bin/bash
# Freeze executable downloader inputs before the unchanged Vim suite can run.
source /opt/toddy-build/scripts/build/h06/common.sh
python3 - <<'PY'
import bz2,gzip,hashlib,json,os
from pathlib import Path
import shutil,subprocess,tarfile
root=Path('/opt/toddy-build');target=Path('/mnt/lfs')
manifest=json.loads((root/'config/vim-glvs-inputs.lock.json').read_text())
base=target/'sources/test-inputs/vim-glvs'
assert not base.is_symlink()
(base/'bin').mkdir(parents=True,exist_ok=True)
(base/'payloads').mkdir(exist_ok=True)
def protected_copy(source,destination,mode):
 if destination.exists() or destination.is_symlink():
  assert not destination.is_symlink() and destination.stat().st_uid==0
  assert destination.read_bytes()==source.read_bytes(),destination
 else:shutil.copyfile(source,destination)
 os.chmod(destination,mode)
for row in manifest['components']:
 subprocess.run(['python3',str(root/'scripts/build/source.py'),'--verify-only',row['filename']],check=True)
 source=target/'sources'/row['filename'];data=source.read_bytes()
 assert hashlib.sha256(data).hexdigest()==row['sha256'] and len(data)==row['size']
 if row['kind'] in ['vmb','vba.gz']:
  lines=(gzip.decompress(data) if row['kind']=='vba.gz' else data).decode().splitlines()
  assert lines[1:3]==['UseVimball','finish']
  position=3
  while position<len(lines):
   if not lines[position]:position+=1;continue
   name,marker=lines[position].split('\t')
   path=Path(name);assert marker=='[[[1' and not path.is_absolute() and '..' not in path.parts
   position+=int(lines[position+1])+2
  assert position==len(lines)
 elif row['kind']=='tar.xz':
  with tarfile.open(source) as archive:
   assert all(not Path(m.name).is_absolute() and '..' not in Path(m.name).parts and (m.isfile() or m.isdir()) for m in archive.getmembers())
 else:assert row['kind']=='vim.bz2' and bz2.decompress(data).startswith(b'" mrswin.vim:')
 protected_copy(source,base/'payloads'/row['filename'],0o444)
protected_copy(root/'config/vim-glvs-inputs.lock.json',base/'manifest.json',0o444)
protected_copy(root/'scripts/build/h07/verified-vim-curl.py',base/'bin/curl',0o555)
print('Pinned Vim downloader inputs verified; archive paths checked without execution')
PY
chroot_run <<'INNER'
set -euo pipefail
mkdir -p /sources/evidence/h07-vim-glvs-inputs
if [[ -s /sources/evidence/h07-vim-glvs-inputs/download-events.jsonl ]]; then
 cp /sources/evidence/h07-vim-glvs-inputs/download-events.jsonl "/sources/evidence/h07-vim-glvs-inputs/download-events.$(date -u +%Y%m%dT%H%M%S).jsonl"
fi
install -o tester -g tester -m600 /dev/null /sources/evidence/h07-vim-glvs-inputs/download-events.jsonl
su tester -c 'TODDY_VIM_DOWNLOAD_LOG=/sources/evidence/h07-vim-glvs-inputs/download-events.jsonl /usr/bin/python3 -' <<'PY'
import hashlib,json,os,subprocess,tempfile
from pathlib import Path
rows=json.loads(Path('/sources/test-inputs/vim-glvs/manifest.json').read_text())['components']
wrapper='/sources/test-inputs/vim-glvs/bin/curl'
with tempfile.TemporaryDirectory(prefix='toddy-vim-inputs-') as directory:
 for row in rows:
  page=Path(directory)/('page-'+str(row['script_id']))
  payload=Path(directory)/row['upstream_filename']
  for url,path in [(row['page_url'],page),(row['download_url'],payload)]:
   subprocess.run([wrapper,'-s','-o',str(path),url],check=True)
  assert hashlib.sha256(payload.read_bytes()).hexdigest()==row['sha256']
 response=subprocess.check_output([wrapper,'-s','-I','-w','%{http_code}','-o','/dev/null','https://www.vim.org/scripts/download_script.php?src_id=1'],text=True)
 assert response=='200',response
print('Actual unprivileged HTTPS downloads verified for all four frozen versions')
PY
INNER
