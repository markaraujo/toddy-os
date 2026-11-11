"""Retire only redundant RAM promotion after its native archive and payload passed."""
from pathlib import Path
import fcntl,hashlib,json,os,shutil,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from stage_package import payload
T=Path('/mnt/lfs');L=Path('/var/log/toddy/phase2')
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
r=json.loads(Path('/var/log/toddy/build/b02-portal-schema-union-install.success.json').read_text());assert r['recipe_exit']==r['postcheck_exit']==0
p=L/'portal-schema-promotion-retired-1.json';assert not p.exists() and not p.with_suffix('.part').exists()
record=json.loads(Path('/var/log/toddy/packages/gtk_4.22.4-1+toddy14_amd64.json').read_text());assert record['installed']
archive=Path('/var/cache/toddy/packages/gtk_4.22.4-1+toddy14_amd64.deb')
with archive.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==record['archive_sha256']
backing=Path('/run/toddy-samba-client-1/gtk-portal-schema-promotion-1');stage=T/'sources/stage/phase2-gtk-portal-schema-union'
assert not backing.is_symlink() and not stage.is_symlink()
assert subprocess.check_output(['findmnt','-n','-o','FSTYPE','--mountpoint',str(stage)],text=True).strip()=='tmpfs'
assert os.stat(stage).st_ino==os.stat(backing).st_ino and os.stat(stage).st_dev==os.stat(backing).st_dev
actual={k:v for k,v in payload(stage).items() if k!='/DEBIAN' and not k.startswith('/DEBIAN/')};assert actual==record['payload']
state={'state':'retirement-intended','scope':'Only redundant RAM promotion; native installed GTK14 and authenticated archive retained. No source/build/accepted cache deletion.','archive_sha256':record['archive_sha256'],'payload_entries':len(actual),'backing':str(backing),'stage':str(stage)}
def save():
 part=p.with_suffix('.part');part.write_text(json.dumps(state,indent=2)+'\n');part.replace(p)
save();subprocess.run(['umount',str(stage)],check=True);assert not list(stage.iterdir());shutil.rmtree(backing)
state['state']='complete';save();print(json.dumps(state))
