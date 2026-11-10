"""Restore exact accepted receipt bytes from retained controller output, once."""
from pathlib import Path
import fcntl,hashlib,json,os,subprocess
from shared_source_inputs import save,volume

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 assert os.geteuid()==0
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
 log=Path('/var/log/toddy/phase2');journal=log/'mitkrb-worker-receipt-repair-1.json';assert not journal.exists()
 wrong=Path('/var/log/toddy/build/b02-libgtop-install.success.json');worker=log/'mitkrb-shared-scratch-1.json'
 assert not worker.exists() and wrong.resolve()==wrong and not wrong.is_symlink()
 bad=wrong.read_bytes();state=json.loads(bad);base=Path('/mnt/lfs/sources/phase2/work/doxygen-1');volume(base)
 source=base/'toddy-editor-workers/mitkrb-1';target=base.parent/'mitkrb-1'
 assert state['state']=='mounted' and state['source']==str(source) and state['target']==str(target)
 assert state['filesystem_uuid']=='ae4347fb-31fd-4193-a333-0a549e144231'
 assert source.resolve()==source and target.resolve()==target
 assert source.stat().st_ino==target.stat().st_ino==state['source_inode']==12699
 assert source.stat().st_dev==target.stat().st_dev==base.stat().st_dev and target.stat().st_uid==101
 assert subprocess.run(['mountpoint','-q',str(target)]).returncode==0
 controller=log/'b02-libgtop-install-controller.log'
 assert digest(controller)=='8b52d1119c1cb1b66ce6e6d51cd67cc2d896f910e987e323f8b8512f2f5fb7de'
 rows=[]
 for line in controller.read_text().splitlines():
  try:row=json.loads(line)
  except ValueError:continue
  if row.get('step')=='b02-libgtop-install':rows.append(row)
 assert len(rows)==1 and rows[0]['recipe_exit']==rows[0]['postcheck_exit']==0
 restored=(json.dumps(rows[0],indent=2)+'\n').encode()
 expected='6c32a0e6bf67b13e27ae083f2d085a6ec0c03cb71a60138963db52f3699f6c45'
 assert hashlib.sha256(restored).hexdigest()==expected
 proof={'state':'verified','scope':'Log receipts only, no source/compiler/test/package/install replay. Exact original native receipt restored from actual retained controller JSON matching pre-existing published SHA256; actual mounted worker receipt relocated.','native_receipt':str(wrong),'native_original_sha256':expected,'worker_receipt':str(worker),'worker_receipt_sha256':hashlib.sha256(bad).hexdigest(),'worker_inode':12699,'controller_sha256':digest(controller)}
 save(journal,proof)
 part=worker.with_suffix('.part');assert not part.exists();part.write_bytes(bad);part.replace(worker)
 assert digest(worker)==proof['worker_receipt_sha256'] and wrong.read_bytes()==bad
 part=wrong.with_suffix('.repair-part');assert not part.exists();part.write_bytes(restored);part.replace(wrong)
 assert digest(wrong)==expected and digest(worker)==proof['worker_receipt_sha256']
 proof.update(state='complete',native_receipt_byte_exact_to_published_digest=True,worker_receipt_preserved=True);save(journal,proof);print(json.dumps(proof))

if __name__=='__main__':main()
