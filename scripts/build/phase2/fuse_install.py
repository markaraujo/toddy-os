"""Promote qualified FUSE data; declare exactly one standard book SUID helper."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2')
from verify_stage import inspect_stage
R=Path('/opt/toddy-build');T=Path('/mnt/lfs');W=T/'sources/phase2/work/fuse-1';L=Path('/var/log/toddy/phase2');V='3.18.2-1+toddy1'

def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def install(resume=False):
 assert (L/'fuse-stage-2.exit').read_text().strip()=='0'
 r=json.loads((W/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0 and len(r['original_units'])==2 and all(x['exit']==0 for x in r['original_units'])
 stage=W/'stage';inspection=inspect_stage(stage)
 assert {str(p.relative_to(stage)):sha(p) for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}==r['stage_sha256']
 assert subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Version}','linux-kernel'],text=True)=='7.1.8-1+toddy2'
 assert subprocess.run(['chroot',str(T),'dpkg-query','-W','fuse'],capture_output=True).returncode==1
 assert shutil.disk_usage(T).free>=16*1024**3+128*1024**2
 destination=T/'sources/stage/phase2-fuse';receipt=L/'fuse-native-install-1.json'
 if resume:
  failed=json.loads(Path('/var/log/toddy/build/b02-fuse-install.failed.json').read_text());assert failed['recipe_exit']==1 and failed['postcheck_exit'] is None and failed['changed_paths']==0
  assert 'Unreviewed payload privilege or ownership: /usr/bin/fusermount3' in Path('/var/log/toddy/build/b02-fuse-install.log').read_text()
  assert receipt.exists() and destination.is_dir() and not destination.is_symlink()
  assert not (destination/'DEBIAN').exists()
  assert not Path('/var/cache/toddy/packages/fuse_'+V+'_amd64.deb').exists() and not Path('/var/log/toddy/packages/fuse_'+V+'_amd64.json').exists()
  for name,digest in r['stage_sha256'].items():assert sha(destination/name)==digest
  for p in destination.rglob('*'):
   name=str(p.relative_to(destination))
   assert name in inspection['entries'] or name.startswith('usr/share/doc/fuse/') or name in ['etc','etc/fuse.conf','usr/share/doc','usr/share/doc/fuse'],name
 else:assert not destination.exists() and not receipt.exists() and not receipt.with_suffix('.part').exists(),'Inspect actual package/stage; never replay uncertain commit'
 state={'state':'promoting','source_stage_manifest_sha256':inspection['manifest_sha256'],'scope':'Qualified compiler stage promoted with exactly standard root-owned fusermount3 SUID permission per frozen BLFS13.1. Actual kernel mount/signals/privilege/refusal/recovery remain pending.'}
 def save():
  p=receipt.with_suffix('.part');p.write_text(json.dumps(state,indent=2)+'\n');p.replace(receipt)
 save()
 if not resume:shutil.copytree(stage,destination,symlinks=True)
 helper=destination/'usr/bin/fusermount3';assert sha(helper)==r['stage_sha256']['usr/bin/fusermount3'];os.chown(helper,0,0);helper.chmod(0o4755)
 configuration=destination/'etc/fuse.conf';configuration.parent.mkdir(parents=True,exist_ok=True);configuration.write_text('# Default owner-only FUSE mounts. Administrator may review changes.\n#mount_max = 1000\n#user_allow_other\n');configuration.chmod(0o644)
 doc=destination/'usr/share/doc/fuse';doc.mkdir(parents=True,exist_ok=True)
 source=T/'sources/phase2/inputs/fuse-3.18.2'
 for name in ['LICENSE','GPL2.txt','LGPL2.txt']:shutil.copyfile(source/name,doc/name)
 shutil.copyfile(source/'LICENSE',doc/'copyright')
 (doc/'README.Toddy').write_text('Source-built Fuse3.18.2. Only fusermount3 is intentionally root-owned4755, per BLFS13.1; other binaries and libraries have no SUID/SGID/capability. Upstream helper confines ordinary mounts to caller permissions; default fuse.conf leaves allow_other disabled. Exact source GPL2/LGPL2.1/per-file notices accompany package. Existing owned Systemd rule creates /dev/fuse0666; kernel module is separately owned. Do not expose a host device or relax host security to run tests. CLI/ABI checks are not native filesystem/privilege acceptance; real owner mount/signals/refusal/unmount/recovery are separately required. This original README is CC BY4.0, full text accompanies it.\n')
 shutil.copyfile(R/'LICENSES/CC-BY-4.0.txt',doc/'CC-BY-4.0.txt')
 privileged=[str(p.relative_to(destination)) for p in destination.rglob('*') if not p.is_symlink() and p.stat().st_mode&0o6000];assert privileged==['usr/bin/fusermount3']
 state.update(state='installing-native-package',helper_sha256=sha(helper),declared_privileged_paths=privileged);save()
 subprocess.run(['python3',str(R/'scripts/build/stage_package.py'),'fuse',V,str(destination),'--source','fuse-3.18.2.tar.gz','--recipe','scripts/build/phase2/fuse-install.sh','--depends','glibc (>= 2.44-1+toddy1), util-linux (>= 2.42.4-1), linux-kernel (>= 7.1.8-1+toddy2)','--conffile','/etc/fuse.conf','--install'],cwd=R,check=True)
 subprocess.run(['chroot',str(T),'ldconfig'],check=True)
 state['state']='installed-postcheck-pending';save()

def check():
 assert subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Status} ${Version}','fuse'],text=True)=='install ok installed '+V
 r=json.loads(Path('/var/log/toddy/packages/fuse_'+V+'_amd64.json').read_text());assert r['installed']
 privileged=[]
 for name,row in r['payload'].items():
  p=T/name.lstrip('/');s=p.lstat();assert s.st_mode==row['mode'] and s.st_uid==row['uid']==0 and s.st_gid==row['gid']==0,name
  if 'sha256' in row:assert sha(p)==row['sha256'],name
  elif 'symlink' in row:assert os.readlink(p)==row['symlink'],name
  if not p.is_symlink() and s.st_mode&0o6000:privileged.append(name)
 assert privileged==['/usr/bin/fusermount3'] and (T/'usr/bin/fusermount3').stat().st_mode&0o7777==0o4755
 prefix=['setpriv','--no-new-privs','chroot','--userspec=101:101','--groups=101',str(T)]
 version=subprocess.run(prefix+['/usr/bin/fusermount3','--version'],capture_output=True,text=True,timeout=15);assert version.returncode==0 and '3.18.2' in version.stdout
 invalid=subprocess.run(prefix+['/usr/bin/fusermount3','--toddy-invalid-option'],capture_output=True,text=True,timeout=15);assert invalid.returncode!=0
 code="import ctypes; f=ctypes.CDLL('libfuse3.so.4'); assert f.fuse_version()==318; f.fuse_pkgversion.restype=ctypes.c_char_p; assert f.fuse_pkgversion()==b'3.18.2'; print('FUSE318 3.18.2')"
 api=subprocess.run(prefix+['python3','-c',code],capture_output=True,text=True,timeout=15);assert api.returncode==0,(api.stdout,api.stderr)
 configuration=(T/'etc/fuse.conf').read_text();assert not any(line.strip()=='user_allow_other' for line in configuration.splitlines())
 assert not subprocess.check_output(['chroot',str(T),'dpkg','--audit'],text=True).strip();subprocess.run(['chroot',str(T),'apt-get','check'],check=True)
 assert shutil.disk_usage(T).free>=16*1024**3
 p=L/'fuse-native-installed-check-1.json';assert not p.exists();p.write_text(json.dumps({'scope':'Owned native package/payload, sole declared root SUID helper, default owner-only policy, actual UID101/NNP helper version/refusal and libfuse API. No real FUSE mount/signals/root-helper/recovery acceptance yet.','version':V,'archive_sha256':r['archive_sha256'],'payload_entries':len(r['payload']),'privileged_paths':privileged,'helper_version':version.stdout.strip(),'invalid_option_exit':invalid.returncode,'native_library_api':api.stdout.strip(),'target_free':shutil.disk_usage(T).free},indent=2)+'\n')
if __name__=='__main__':
 assert os.getuid()==0 and len(sys.argv)==2
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 {'install':install,'resume-promoted':lambda:install(True),'check':check}[sys.argv[1]]()
