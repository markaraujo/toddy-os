"""Install a fully tested Git stage with hardlinks preserved and no user config."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,tempfile
from verify_stage import inspect_stage
R=Path('/opt/toddy-build');T=Path('/mnt/lfs');L=Path('/var/log/toddy/phase2');W=T/'sources/phase2/work/git-1';V='2.55.0-1+toddy1'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def query(n,fmt='${Version}'):
 return subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f='+fmt,n],text=True)
def install():
 build_exit=(L/'git-build-1.exit').read_text().strip()
 if build_exit!='0':
  assert build_exit=='1' and (L/'git-qualify-2.exit').read_text().strip()=='0'
  assert 'Require original full shell suite result records, not a smoke subset' in (L/'git-build-1.log').read_text()
 r=json.loads((W/'stage-results.json').read_text());assert r['compile_exit']==r['test_exit']==r['stage_exit']==0 and r['original_totals']['failed']==0 and r['original_shell_groups']>500
 assert json.loads((W/'capacity-result.json').read_text())['stop_reason'] is None
 stage=W/'stage';inspection=inspect_stage(stage)
 assert {str(p.relative_to(stage)):sha(p) for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}==r['stage_sha256']
 assert subprocess.run(['chroot',str(T),'dpkg-query','-W','git'],capture_output=True).returncode==1
 dest=T/'sources/stage/phase2-git';receipt=L/'git-native-install-1.json';assert not any(os.path.lexists(p) for p in [dest,receipt,receipt.with_suffix('.part')])
 assert shutil.disk_usage(T).free>=16*1024**3+128*1024**2
 depends=', '.join(n+' (= '+query(n)+')' for n in ['glibc','curl','expat','pcre2','perl','python','zlib','openssl','ca-certificates','bash','coreutils'])
 state={'state':'promotion-intended','manifest_sha256':inspection['manifest_sha256'],'depends':depends,'scope':'Full upstream-tested C-only Git CLI. Preserve hardlinks and user/system configuration; optional Tcl/Tk GUI omitted.'}
 def save():
  p=receipt.with_suffix('.part');p.write_text(json.dumps(state,indent=2)+'\n');p.replace(receipt)
 save();subprocess.run(['cp','-a','--reflink=auto',str(stage),str(dest)],check=True);os.chown(dest,0,0)
 classes={};reverse={}
 for p in stage.rglob('*'):
  if p.is_file() and not p.is_symlink():
   q=dest/p.relative_to(stage);a=(p.stat().st_dev,p.stat().st_ino);b=(q.stat().st_dev,q.stat().st_ino)
   assert classes.setdefault(a,b)==b and reverse.setdefault(b,a)==a
 doc=dest/'usr/share/doc/git';doc.mkdir(parents=True,exist_ok=True)
 source=T/'sources/phase2/inputs/git-2.55.0'
 for f in ['COPYING','README.md','Documentation/git.adoc','Documentation/gittutorial.adoc']:shutil.copyfile(source/f,doc/Path(f).name)
 shutil.copyfile(source/'COPYING',doc/'copyright')
 state.update(state='installing-native-package',preserved_hardlink_classes=len(classes));save()
 subprocess.run(['python3',str(R/'scripts/build/stage_package.py'),'git',V,str(dest),'--source','git-2.55.0.tar.xz','--recipe','scripts/build/phase2/git-install.sh','--depends',depends,'--install'],cwd=R,check=True)
 state['state']='installed-postcheck-pending';save()
def check():
 assert query('git','${Status} ${Version}')=='install ok installed '+V
 record=json.loads(Path('/var/log/toddy/packages/git_'+V+'_amd64.json').read_text());assert record['installed']
 for n,row in record['payload'].items():
  p=T/n.lstrip('/');s=p.lstat();assert (s.st_mode,s.st_uid,s.st_gid)==(row['mode'],0,0),n
  if 'sha256' in row:assert sha(p)==row['sha256'],n
  elif 'symlink' in row:assert os.readlink(p)==row['symlink'],n
  if not p.is_symlink():assert not s.st_mode&0o6000,n
 assert not subprocess.check_output(['chroot',str(T),'dpkg','--audit'],text=True).strip();subprocess.run(['chroot',str(T),'apt-get','check'],check=True)
 with tempfile.TemporaryDirectory(prefix='toddy-git-check-',dir=T/'tmp') as temp:
  p=Path(temp);os.chown(p,101,101);p.chmod(0o755);virtual='/tmp/'+p.name
  code=(R/'scripts/build/phase2/git_native_consumer.py').read_text()
  wrapper='set -euo pipefail; mount --make-rprivate /; mount -t tmpfs -o size=1m,nosuid,nodev tmpfs /mnt/lfs/dev; for name in null zero random urandom; do touch /mnt/lfs/dev/$name; mount --bind /dev/$name /mnt/lfs/dev/$name; done; mount -t proc proc /mnt/lfs/proc; exec setpriv --no-new-privs chroot --userspec=101:101 --groups=101 /mnt/lfs python3 -c "$1" "$2"'
  actual=subprocess.run(['unshare','--mount','--pid','--fork','--net','bash','-c',wrapper,'git-check',code,virtual],capture_output=True,text=True,timeout=60)
  assert actual.returncode==0,(actual.stdout,actual.stderr)
  proof=json.loads(actual.stdout)
 receipt=L/'git-native-installed-check-1.json';assert not receipt.exists();receipt.write_text(json.dumps({'scope':'Owned actual installed native UID101/NNP Git offline repository/clone/merge/dirty-checkout refusal/fsck and credential prompt refusal. Original full isolated upstream suite is separate. No external remote/credential/helper/provider service tested.','archive_sha256':record['archive_sha256'],'payload_entries':len(record['payload']),'consumer':proof},indent=2)+'\n')
if __name__=='__main__':
 assert os.getuid()==0 and len(sys.argv)==2
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 {'install':install,'check':check}[sys.argv[1]]()
