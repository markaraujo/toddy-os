#!/bin/bash
# One-time migration of the accepted foundation's generated default-target state.
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,subprocess
T=Path('/mnt/lfs');L=Path('/var/log/toddy/phase2');receipt=L/'desktop-graphical-boot-1.json'
assert not receipt.exists() and not receipt.with_suffix('.part').exists(),'Inspect generated links/receipt; never replay'
def ctl(*args):
 p=subprocess.run(['chroot',str(T),'systemctl','--root=/','--no-reload',*args],capture_output=True,text=True)
 assert p.returncode==0,(args,p.returncode,p.stdout,p.stderr)
 return {'args':list(args),'stdout':p.stdout,'stderr':p.stderr}
def provider(package,unit):
 version=subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Version}',package],text=True)
 r=json.loads(Path('/var/log/toddy/packages',package+'_'+version+'_amd64.json').read_text());assert r['installed']
 expected=r['payload']['/usr/lib/systemd/system/'+unit]['sha256']
 p=T/'usr/lib/systemd/system'/unit;assert not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==expected
 return {'version':version,'archive_sha256':r['archive_sha256'],'unit_sha256':expected}
default=T/'etc/systemd/system/default.target';manager=T/'etc/systemd/system/display-manager.service'
assert default.is_symlink() and default.readlink()==Path('/usr/lib/systemd/system/multi-user.target'),'Preserve an owner-selected default'
assert not os.path.lexists(manager),'Preserve an existing display manager'
assert subprocess.run(['chroot',str(T),'dpkg-query','-S','/etc/systemd/system/default.target'],capture_output=True).returncode==1,'Do not overwrite package payload'
assert (T/'etc/systemd/system/systemd-networkd-wait-online.service').is_symlink()
assert (T/'etc/systemd/system/systemd-networkd-wait-online.service').readlink()==Path('/dev/null')
r={'state':'enabling-owned-display-manager','scope':'Generated native Systemd boot configuration only; no unit/PAM/security/user-profile mutation. One-time exact foundation multi-user default migration; future user-selected targets are not reset.',
   'before_default':str(default.readlink()),'providers':{'gdm':provider('gdm','gdm.service'),'systemd':provider('systemd','graphical.target')},'operations':[]}
def save():
 part=receipt.with_suffix('.part')
 with part.open('x') as f:json.dump(r,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 part.replace(receipt)
save();r['operations'].append(ctl('enable','gdm.service'))
assert manager.is_symlink() and manager.readlink()==Path('/usr/lib/systemd/system/gdm.service')
r['state']='selecting-graphical-default';save();r['operations'].append(ctl('set-default','graphical.target'))
assert default.is_symlink() and default.readlink()==Path('/usr/lib/systemd/system/graphical.target')
assert ctl('get-default')['stdout'].strip()=='graphical.target'
assert ctl('is-enabled','gdm.service')['stdout'].strip()=='enabled'
r.update(state='complete',after_default=str(default.readlink()),display_manager=str(manager.readlink()),
 recovery='Inspect actual receipt/links first. Before reverting only these generated links, verify they still equal recorded after values; use native systemctl --root to disable gdm and restore recorded multi-user default. Preserve any later owner change. No rollback executed.',
 native_boot_verified=False)
save();print(json.dumps(r))
PY
