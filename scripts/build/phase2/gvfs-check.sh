#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,subprocess,sys,tempfile
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2')
from qualify_gvfs import qualify,digest,EXCLUDED
T=Path('/mnt/lfs');prefix=['chroot',str(T)];proof=qualify(Path('/opt/toddy-build'))
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','gvfs'],text=True)=='install ok installed 1.60.2-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip()
subprocess.run(prefix+['apt-get','check'],check=True)
for name,sha in proof['stage_sha256'].items():
 if name in EXCLUDED:assert not (T/name).exists()
 else:assert digest(T/name)==sha
stage=T/'sources/phase2/work/gvfs-1/stage';elfs=[]
for p in stage.rglob('*'):
 name=str(p.relative_to(stage))
 if name in EXCLUDED:continue
 if p.is_symlink():assert os.readlink(T/name)==os.readlink(p)
 elif p.is_file():
  assert not p.stat().st_mode&0o6000
  if p.open('rb').read(4)==b'\x7fELF':elfs.append(name)
assert len(elfs)==21
for name in elfs:
 linked=subprocess.check_output(prefix+['ldd','/'+name],text=True)
 assert 'not found' not in linked and not any(v in linked for v in ['/sources/','/src/','/build/'])
with tempfile.TemporaryDirectory(prefix='toddy-gvfs-check-',dir=T/'var/tmp') as d:
 os.chown(d,101,101);home='/var/tmp/'+Path(d).name
 env={'PATH':'/usr/bin:/usr/sbin','HOME':home,'LC_ALL':'C.UTF-8'}
 base=['setpriv','--no-new-privs','chroot','--userspec=101:101','--groups=101',str(T)]
 rows=[]
 for args,expected in [(['/usr/libexec/gvfsd','--version'],0),(['/usr/libexec/gvfsd','--toddy-no-such-option'],1),(['/usr/libexec/gvfsd','--help'],0),(['/usr/libexec/gvfsd','--version'],0),(['/usr/libexec/gvfsd-admin'],1)]:
  r=subprocess.run(base+args,env=env,capture_output=True,text=True,timeout=15)
  assert r.returncode==expected,(args,r.returncode,r.stderr)
  if args[-1]=='--version':assert r.stdout=='gvfs 1.60.2\n'
  if args[0].endswith('gvfsd-admin'):assert 'must be executed under pkexec' in r.stderr
  rows.append({'args':args,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
policy=T/'usr/share/polkit-1/actions/org.gtk.vfs.file-operations.policy'
import xml.etree.ElementTree as ET
actions=ET.parse(policy).findall('action');assert len(actions)==2
for a in actions:
 assert a.findtext('defaults/allow_any')=='no' and a.findtext('defaults/allow_inactive')=='no'
 assert a.findtext('defaults/allow_active')=='auth_admin_keep'
# The upstream wheel rule authorizes only helper startup; per-client file
# operations still require the distinct authenticated action above.
rules=(T/'usr/share/polkit-1/rules.d/org.gtk.vfs.file-operations.rules').read_text()
assert 'org.gtk.vfs.file-operations-helper' in rules and 'subject.isInGroup ("wheel")' in rules
assert 'action.id == "org.gtk.vfs.file-operations"' not in rules
selection=json.loads(Path('/var/log/toddy/phase2/gvfs-runtime-selection.json').read_text())
assert digest(T/'usr/lib/gio/modules/giomodule.cache')==selection['GIO_cache_sha256']
result={'scope':'Owned Gvfs exact payload/ABI/APT/CLI refusal-recovery,unauthenticated admin refusal and original upstream authenticated action policy. Reuses17local cases; original baseline append-tell remains failed. Native backend activation/Trash GUI/privilege mediation remain unqualified. SFTP omitted until owned SSH client exists; no backend started or policy relaxed.',
 'identical_regular_files':131,'installed_ELFs':21,'no_suid_sgid':True,'cli':rows,'shared_GIO_cache_changed':False,'sftp_unavailable':True}
Path('/var/log/toddy/phase2/gvfs-installed-consumer.json').write_text(json.dumps(result,indent=2)+'\n')
PY
