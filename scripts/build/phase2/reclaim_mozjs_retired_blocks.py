"""One NEW virtual free-block generation after verified Mozilla source custody."""
import fcntl,hashlib,json,os,stat,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from run_step import snapshot
from phase2.virtual_discard_checkpoint import save
LOG=Path('/var/log/toddy/phase2');RECEIPT=LOG/'mozjs-baseline-source-discard-1.json'
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pending():
 result={}
 for name in ['accountsservice-1','upower-1','gnome-session-1']:
  work=Path('/mnt/lfs/sources/phase2/work')/name
  for base in [work/'stage',work/'compile']:
   assert base.is_dir() and not base.is_symlink()
   for p in base.rglob('*'):
    st=p.lstat();row={'mode':st.st_mode,'uid':st.st_uid,'gid':st.st_gid}
    if p.is_symlink():row['symlink']=str(p.readlink())
    elif p.is_file():row['sha256']=digest(p)
    else:assert p.is_dir()
    result[str(p.relative_to('/mnt/lfs'))]=row
  result[str((work/'stage-results.json').relative_to('/mnt/lfs'))]={'sha256':digest(work/'stage-results.json')}
 assert result;return result
def main():
 assert os.geteuid()==0 and not RECEIPT.exists(),'Reconcile actual prior state; never repeat an uncertain trim'
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
 assert subprocess.check_output(['findmnt','-n','-o','SOURCE','--mountpoint','/mnt/lfs'],text=True).strip()=='/dev/vdb4'
 assert subprocess.check_output(['lsblk','-dnro','SERIAL','/dev/vdb'],text=True).strip()=='TODDY-LFS-TARGET'
 assert int(Path('/sys/class/block/vdb/queue/discard_max_bytes').read_text())>0
 assert json.loads((LOG/'virtual-target-discard.json').read_text())['state']=='complete','Old generation must be complete, never resumed here'
 custody=json.loads((LOG/'mozjs-baseline-source-custody-1.json').read_text());assert custody['state']=='complete' and custody['source_unchanged'] and custody['restored_exact'] and custody['installed_root_changed_paths']==0
 assert custody['reclaimed_target_bytes']==4368916480 and custody['archive_sha256']=='0034632f70329e0bdf92f5d6fdd4cd9d08721f041f989abee65bfc5e5655dea6'
 source=Path(custody['source']);assert source==Path('/mnt/lfs/sources/phase2/inputs/mozjs-tool-140.14.0') and not source.is_symlink() and [p.name for p in source.iterdir()]==['.toddy-retired.json']
 archive=Path(custody['archive']);assert archive.is_file() and not archive.is_symlink() and digest(archive)==custody['archive_sha256']
 for name in ['accountsservice','upower','gnome-session']:
  accepted=json.loads((LOG.parent/'build'/('b02-'+name+'-install.success.json')).read_text());assert accepted['recipe_exit']==accepted['postcheck_exit']==0
 before=snapshot();cached=pending();save(LOG/'mozjs-baseline-source-discard-1-before-root.json',before,private=True);save(LOG/'mozjs-baseline-source-discard-1-before-pending.json',cached,private=True)
 r={'scope':'NEW free-block discard after completed Mozilla baseline source custody; exact virtual /dev/vdb4 only, no formatting/source deletion/physical-host operation; older discard/custody never replayed','state':'checkpointed','pid':os.getpid(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'proc_start_ticks':Path('/proc/self/stat').read_text().split()[21],'producer_sha256':digest(Path(__file__)),'started_unix':time.time(),'custody_receipt_sha256':digest(LOG/'mozjs-baseline-source-custody-1.json'),'archive_sha256':custody['archive_sha256'],'root_entries':len(before),'pending_entries':len(cached),'recovery':'Inspect durable receipt, real process start identity, trim log and .exit before any action. Never repeat trim_running/trim_done; reconcile snapshots and archive against retained before manifests. Old main/trim/custody commands must not run.'}
 save(RECEIPT,r);r['state']='trim_running';save(RECEIPT,r)
 with (LOG/'mozjs-baseline-source-discard-1.log').open('xb') as out:
  result=subprocess.run(['fstrim','--verbose','/mnt/lfs'],stdout=out,stderr=subprocess.STDOUT);out.flush();os.fsync(out.fileno())
 (LOG/'mozjs-baseline-source-discard-1.exit').write_text(str(result.returncode)+'\n');r.update(state='trim_done' if result.returncode==0 else 'trim_failed',trim_exit=result.returncode);save(RECEIPT,r);assert result.returncode==0
 after=snapshot();cached_after=pending();changed=[p for p in before.keys()|after.keys() if before.get(p)!=after.get(p)];cache_changed=[p for p in cached.keys()|cached_after.keys() if cached.get(p)!=cached_after.get(p)]
 archive_same=digest(archive)==custody['archive_sha256'];r.update(changed_paths=changed,pending_changed_paths=cache_changed,archive_unchanged=archive_same,finished_unix=time.time(),state='complete' if not changed and not cache_changed and archive_same else 'verification_failed');save(RECEIPT,r)
 assert r['state']=='complete','Preserve differences; no repeat trim';print(json.dumps(r))
if __name__=='__main__':main()
