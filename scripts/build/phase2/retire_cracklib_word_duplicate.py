"""Retain exact compressed dictionary source; retire its verified decoded duplicate."""
from pathlib import Path
import fcntl,hashlib,json,lzma,os,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from run_step import snapshot
from qualify_cracklib import qualify,digest
from shared_source_inputs import save

def main():
 assert os.geteuid()==0
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
 receipt=Path('/var/log/toddy/phase2/cracklib-word-source-custody-1.json');assert not receipt.exists()
 root=Path('/opt/toddy-build');proof=qualify(root)
 success=json.loads(Path('/var/log/toddy/build/b02-cracklib-install.success.json').read_text());assert success['recipe_exit']==success['postcheck_exit']==0
 raw=Path('/mnt/lfs/sources/phase2/work/cracklib-1/original-words')
 compressed=Path('/mnt/lfs/sources/phase2/inputs/cracklib-2.10.3/toddy-words.xz')
 assert raw.resolve()==raw and raw.is_file() and not raw.is_symlink() and raw.stat().st_size==19163351
 expected='72850d6a542578ccedc74088bbe31ce2a872bf447ea61d05661879b8430c5f6f'
 packed='b3d1e0e0ae9bc7ffed65c0042d7c68bdb903368aa6b918f94572453c6ea874dc'
 assert digest(raw)==expected and digest(compressed)==packed
 h=hashlib.sha256();size=0
 with lzma.open(compressed,'rb') as stream:
  while block:=stream.read(1024*1024):
   size+=len(block);assert size<=19163351;h.update(block)
 assert size==19163351 and h.hexdigest()==expected
 before=snapshot();v=os.statvfs('/mnt/lfs');free=v.f_bavail*v.f_frsize
 state={'state':'verified','scope':'Only decoded dictionary duplicate; exact compressed source, source notices, compiler/stage/tests/native archive/installed root retained; no install or trim',
        'raw':str(raw),'raw_inode':raw.stat().st_ino,'expanded_sha256':expected,'expanded_bytes':size,
        'compressed':str(compressed),'compressed_sha256':packed,'before_free':free}
 save(receipt,state);state['state']='retiring';save(receipt,state)
 assert raw.stat().st_ino==state['raw_inode'];raw.unlink();state['state']='retired';save(receipt,state)
 assert not raw.exists() and digest(compressed)==packed and qualify(root)==proof and snapshot()==before
 v=os.statvfs('/mnt/lfs');state.update(state='complete',installed_root_changed_paths=0,after_free=v.f_bavail*v.f_frsize,
     recovery='Decode retained authenticated xz to a NEW bounded location, verify exact expanded length/hash before restoring any absent cache path; no compiler/test/install replay')
 state['reclaimed_bytes']=state['after_free']-free;save(receipt,state);print(json.dumps(state))

if __name__=='__main__':main()
