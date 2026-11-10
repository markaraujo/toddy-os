"""Retire only named private linker temporaries after verified terminal artifacts."""
from pathlib import Path
import fcntl,hashlib,json,os,stat,subprocess
W=Path('/mnt/lfs/sources/phase2/work/kernel-landlock-1');P=Path('/var/log/toddy/phase2')
NAMES=['.tmp_vmlinux1','.tmp_vmlinux2','.tmp_vmlinux1.kallsyms.S','.tmp_vmlinux2.kallsyms.S','.tmp_vmlinux.nm-sort']
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 assert os.getuid()==0
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not list(Path('/var/log/toddy/build').glob('*.running.json')) and (P/'kernel-landlock-build-4.exit').read_text().strip()=='0'
 assert json.loads((P/'kernel-landlock-lower-retained-1.json').read_text())['unchanged_entries']==111558
 receipt=P/'kernel-landlock-temporary-retirement-1.json';assert not receipt.exists() and not receipt.with_suffix('.part').exists(),'Reconcile actual partial retirement; never replay uncertain deletion'
 baseline=json.loads((W/'baseline.json').read_text());artifacts=json.loads((W/'kernel-build-4/artifacts.json').read_text())
 for name,sha in artifacts.items():assert digest(W/'merged'/name)==sha
 rows={}
 for name in NAMES:
  assert name not in baseline['pristine_source'] and name not in artifacts
  p=W/'merged'/name;u=W/'private-overlay/upper'/name;s=p.lstat();assert stat.S_ISREG(s.st_mode) and not u.is_symlink() and u.is_file() and 'trusted.overlay.metacopy' not in os.listxattr(u)
  rows[name]={'sha256':digest(p),'bytes':s.st_size,'inode':s.st_ino,'links':s.st_nlink}
 result={'state':'retirement-intended','scope':'Only five fixed private linker intermediates after actual compile0/full original cache retention; original source/cache and final artifacts preserved','files':rows,'free_before':os.statvfs(W).f_bavail*os.statvfs(W).f_frsize,'final_artifacts':artifacts}
 def save():
  part=receipt.with_suffix('.part');part.write_text(json.dumps(result,indent=2)+'\n');part.replace(receipt)
 save()
 for name,record in rows.items():
  p=W/'merged'/name;assert digest(p)==record['sha256'] and p.stat().st_ino==record['inode'];p.unlink()
 for name,sha in artifacts.items():assert digest(W/'merged'/name)==sha
 result.update(state='complete',free_after=os.statvfs(W).f_bavail*os.statvfs(W).f_frsize,final_artifacts_unchanged=True);assert result['free_after']>=128*1024**2;save();print(json.dumps(result))
if __name__=='__main__':main()
