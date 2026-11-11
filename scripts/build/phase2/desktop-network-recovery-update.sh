#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'INNER'
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
R=Path('/opt/toddy-build');T=Path('/mnt/lfs');L=Path('/var/log/toddy/phase2')
sys.path.insert(0,str(R/'scripts/build/phase2'));from desktop_network import stage
sys.path.insert(0,str(R/'scripts/build'));from stage_package import payload
name='toddy-desktop-network';oldversion='0.2.0-1+toddy1';newversion='0.2.0-1+toddy2'
old=json.loads(Path('/var/log/toddy/packages',name+'_'+oldversion+'_all.json').read_text())
assert old['installed']
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Version}',name],text=True)==oldversion
for n,row in old['payload'].items():
 p=T/n.lstrip('/');st=p.lstat();assert (st.st_mode,st.st_uid,st.st_gid)==(row['mode'],row['uid'],row['gid']),n
 if 'sha256' in row:assert digest(p)==row['sha256'],n
 elif 'symlink' in row:assert os.readlink(p)==row['symlink'],n
oldarchive=Path('/var/cache/toddy/packages',name+'_'+oldversion+'_all.deb')
assert digest(oldarchive)==old['archive_sha256']
receipt=L/'desktop-network-recovery-update-1.json';destination=T/'sources/stage/phase2-toddy-network-recovery-1'
assert not receipt.exists() and not destination.exists(),'Inspect actual receipt/package; never replay'
for base,suffix in [('/var/log/toddy/packages','.json'),('/var/cache/toddy/packages','.deb')]:
 assert not Path(base,name+'_'+newversion+'_all'+suffix).exists()
assert shutil.disk_usage(T).free>=16*1024**3+2*1024**2
conffiles=stage(destination,R);updated=payload(destination);readme='/usr/share/doc/toddy-desktop-network/README'
assert set(updated)==set(old['payload'])
assert updated[readme]!=old['payload'][readme]
for n in updated:
 if n!=readme:assert updated[n]==old['payload'][n],n
state={'state':'installing','scope':'README-only owned correction for actual native networkd socket reactivation; no service/configuration/binary/profile mutation','old_archive_sha256':old['archive_sha256'],'unchanged_payload_entries':len(updated)-1,'changed_path':readme,'old_readme_sha256':old['payload'][readme]['sha256'],'new_readme_sha256':updated[readme]['sha256']}
def save():receipt.write_text(json.dumps(state,indent=2)+'\n')
save()
depends=subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Depends}',name],text=True)
command=[sys.executable,str(R/'scripts/build/stage_package.py'),name,newversion,str(destination),'--architecture','all','--recipe','scripts/build/phase2/desktop-network-recovery-update.sh','--depends',depends]
for n in conffiles:command+=['--conffile',n]
subprocess.run(command+['--install'],cwd=R,check=True)
new=json.loads(Path('/var/log/toddy/packages',name+'_'+newversion+'_all.json').read_text());assert new['installed'] and new['payload']==updated
state.update(state='complete',archive_sha256=new['archive_sha256']);save()
INNER
