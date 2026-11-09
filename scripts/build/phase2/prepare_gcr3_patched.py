"""Prepare a new source/work identity for the disabled-feature Meson correction."""
import fcntl,hashlib,json,os,shutil,subprocess
from pathlib import Path
ROOT=Path('/opt/toddy-build');LOG=Path('/var/log/toddy/phase2')
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def tree(base):
 return {str(p.relative_to(base)):({'symlink':str(p.readlink())} if p.is_symlink() else {'sha256':digest(p),'mode':p.stat().st_mode&0o7777}) for p in base.rglob('*') if p.is_file() or p.is_symlink()}
def main():
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
 patch=json.loads((ROOT/'config/phase2/gcr3-patches.lock.json').read_text());assert digest(ROOT/patch['patch_file'])==patch['patch_sha256']
 source=Path('/mnt/lfs/sources/phase2/inputs/gcr-3.41.2');new=source.with_name('gcr-3.41.2-ssh-agent-1');work=Path('/mnt/lfs/sources/phase2/work/gcr3-patched-1');receipt=LOG/'gcr3-patched-input-1.json'
 assert not any(p.exists() for p in [new,work,receipt]),'Reconcile existing patch preparation; no replay'
 assert (LOG/'gcr3-1.exit').read_text().strip()=='1' and 'Unable to get the path of a not-found external program' in (LOG/'gcr3-1.log').read_text()
 for name in ['build.ninja','meson-private/coredata.dat','config.h']:assert not (Path('/mnt/lfs/sources/phase2/work/gcr3-1/compile')/name).exists()
 assert digest(source/patch['path'])==patch['before_sha256']
 original=tree(source);data={'state':'copying','scope':'New isolated Gcr3 input; original source/failed configure logs retained, no library compiler or package replay','source':str(source),'input':str(new),'work':str(work),'source_entries':len(original),'source_manifest_sha256':hashlib.sha256(json.dumps(original,sort_keys=True).encode()).hexdigest(),'patch':patch}
 def save():receipt.write_text(json.dumps(data,indent=2)+'\n')
 save();shutil.copytree(source,new,symlinks=True);assert tree(new)==original==tree(source)
 subprocess.run(['patch','--batch','--forward','--fuzz=0','-Np1','-i',str(ROOT/patch['patch_file'])],cwd=new,check=True)
 assert digest(new/patch['path'])==patch['after_sha256'];changed=[name for name,row in tree(new).items() if original.get(name)!=row];assert changed==['meson.build']
 prepared=json.loads((new/'toddy-prepared.json').read_text());prepared['source_patches'].append(patch);(new/'toddy-prepared.json').write_text(json.dumps(prepared,indent=2)+'\n')
 work.mkdir();os.chown(work,101,101);assert tree(source)==original
 data.update(state='complete',changed_source_paths=changed,original_source_unchanged=True);save();print(json.dumps({k:data[k] for k in ['state','input','work','source_entries','changed_source_paths','original_source_unchanged']}))
if __name__=='__main__':main()
