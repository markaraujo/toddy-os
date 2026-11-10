"""Commit only the prepared and fully verified native kernel archive once."""
from pathlib import Path
import json,os,subprocess,sys
sys.path.insert(0,'/opt/toddy-build/scripts/build')
from package_backend import PackageBackend
from qualify_kernel_landlock_stage import W,L,digest,KERNEL_SHA
T=Path('/mnt/lfs');V='7.1.8-1+toddy1';archive=Path('/var/cache/toddy/packages/linux-kernel_'+V+'_amd64.deb');record=Path('/var/log/toddy/packages/linux-kernel_'+V+'_amd64.json')
assert os.getuid()==0
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
passed=json.loads(Path('/var/log/toddy/build/b02-linux-kernel-landlock-package.success.json').read_text());assert passed['recipe_exit']==passed['postcheck_exit']==0
qa=json.loads((L/'kernel-landlock-archive-verified-1.json').read_text());r=json.loads(record.read_text());assert not r['installed'] and digest(archive)==r['archive_sha256']==qa['archive_sha256']
assert r['payload']['/boot/vmlinuz-7.1.8-toddy']['sha256']==KERNEL_SHA and not any(x.startswith('/usr/share/info/') for x in r['payload'])
assert subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Status} ${Version}','linux-kernel'],text=True)=='install ok installed 7.1.8-1'
old=json.loads(Path('/var/log/toddy/packages/linux-kernel_7.1.8-1_amd64.json').read_text())
for stem in ['vmlinuz','config','System.map']:
 name='/boot/'+stem+'-7.1.8-toddy';assert digest(T/name.lstrip('/'))==old['payload'][name]['sha256']
assert os.statvfs(T).f_bavail*os.statvfs(T).f_frsize>=16*1024**3+archive.stat().st_size+40*1024**2
receipt=L/'kernel-landlock-native-commit-1.json';assert not receipt.exists() and not receipt.with_suffix('.part').exists(),'Reconcile actual package status; never repeat uncertain native commit'
state={'state':'install-intended','archive_sha256':r['archive_sha256'],'old_version':'7.1.8-1','new_version':V}
def save():
 p=receipt.with_suffix('.part');p.write_text(json.dumps(state,indent=2)+'\n');p.replace(receipt)
save();PackageBackend(T).install(archive)
r['installed']=True;part=record.with_suffix('.part');part.write_text(json.dumps(r,indent=2)+'\n');part.replace(record)
state['state']='installed-postcheck-pending';save()
