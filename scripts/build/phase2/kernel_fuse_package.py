"""Controlled native FUSE kernel package, retaining verified prior payload/recovery."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,tarfile
sys.path.insert(0,'/opt/toddy-build/scripts/build')
from package_backend import PackageBackend
T=Path('/mnt/lfs');R=Path('/opt/toddy-build');W=T/'sources/phase2/work/kernel-landlock-1';L=Path('/var/log/toddy/phase2');P=Path('/var/log/toddy/packages');C=Path('/var/cache/toddy/packages')
OLD='7.1.8-1+toddy1';NEW='7.1.8-1+toddy2';KERNEL='0482366cc51727f76af11611275b7124bcd9aadbd76d231ca6fd44d22cb0dc77';MODULE='ce3b8f53643839d98fec304561376bf3c6ae873c519468a57b15f3e723111ae2'

def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def record(version):return json.loads((P/('linux-kernel_'+version+'_amd64.json')).read_text())
def archive(version):return C/('linux-kernel_'+version+'_amd64.deb')
def native(*args):
 p=subprocess.run(['chroot',str(T),*args],capture_output=True,text=True)
 if p.returncode:print(p.stdout,p.stderr,file=sys.stderr)
 p.check_returncode();return p
def owned(root,r):
 for name,row in r['payload'].items():
  p=root/name.lstrip('/');s=p.lstat();assert s.st_mode==row['mode'] and s.st_uid==row['uid']==0 and s.st_gid==row['gid']==0,name
  if 'sha256' in row:assert sha(p)==row['sha256'],name
  elif 'symlink' in row:assert p.is_symlink() and os.readlink(p)==row['symlink'],name

def prepare():
 old=record(OLD);assert old['installed'] and sha(archive(OLD))==old['archive_sha256']
 assert native('dpkg-query','-W','-f=${Version}','linux-kernel').stdout==OLD
 owned(T,old)
 proof=json.loads((L/'kernel-fuse-native-acceptance-2.json').read_text())
 assert proof['result']['complete'] and {r['firmware'] for r in proof['result']['runs']}=={'bios','uefi'}
 assert all(r['exit']==0 and r['kernel_boot_verified'] and not r['target_disks_attached'] for r in proof['result']['runs'])
 assert proof['prepared']['kernel_sha256']==KERNEL and proof['prepared']['fuse_module_sha256']==MODULE
 a=json.loads((W/'kernel-fuse-build-2/artifacts.json').read_text())
 for name,digest in a.items():assert sha(W/'merged'/name)==digest,name
 assert a['arch/x86/boot/bzImage']==KERNEL and a['fs/fuse/fuse.ko']==MODULE
 assert not archive(NEW).exists() and not (P/('linux-kernel_'+NEW+'_amd64.json')).exists()
 assert shutil.disk_usage(T).free>=16*1024**3+128*1024**2 and shutil.disk_usage(W).free>=384*1024**2
 stage=W/'stage';destination=T/'sources/stage/phase2-linux-kernel-fuse';receipt=L/'kernel-fuse-package-prepared-1.json'
 assert stage.is_dir() and not stage.is_symlink() and not list(stage.iterdir())
 assert not receipt.exists() and not receipt.with_suffix('.part').exists() and not os.path.lexists(destination),'Inspect existing stage/archive before retry'
 state={'state':'staging-intended','old_archive_sha256':old['archive_sha256'],'scope':'Data-only native staging from actual qualified archive and UID101-built/booted candidate; installed payload unchanged until explicit controlled commit.'}
 def save():
  p=receipt.with_suffix('.part');p.write_text(json.dumps(state,indent=2)+'\n');p.replace(receipt)
 save();subprocess.run(['dpkg-deb','--extract',str(archive(OLD)),str(stage)],check=True);owned(stage,old)
 assert {'/'+str(p.relative_to(stage)) for p in stage.rglob('*')}==set(old['payload'])
 backups={}
 for stem,source in [('vmlinuz','arch/x86/boot/bzImage'),('config','.config'),('System.map','System.map')]:
  p=stage/'boot'/(stem+'-7.1.8-toddy');backup=p.with_name(p.name+'-pre-fuse');assert not backup.exists()
  shutil.copyfile(p,backup);backup.chmod(0o644);backups['/'+str(backup.relative_to(stage))]=sha(backup)
  shutil.copyfile(W/'merged'/source,p);p.chmod(0o644)
 prefix='usr/lib/modules/7.1.8-toddy';module=stage/prefix/'kernel/fs/fuse/fuse.ko';assert not module.exists()
 module.parent.mkdir(parents=True);shutil.copyfile(W/'merged/fs/fuse/fuse.ko',module);module.chmod(0o644)
 order=(W/'merged/modules.order').read_text().splitlines();assert len(order)==21 and all(n.endswith('.o') for n in order)
 (stage/prefix/'modules.order').write_text(''.join(n[:-2]+'.ko\n' for n in order))
 native('depmod','-b','/sources/phase2/work/kernel-landlock-1/stage','-m','/usr/lib/modules','-F','/sources/phase2/work/kernel-landlock-1/stage/boot/System.map-7.1.8-toddy','7.1.8-toddy')
 oldmodules={n:row['sha256'] for n,row in old['payload'].items() if n.endswith('.ko')};assert len(oldmodules)==20
 for name,digest in oldmodules.items():assert sha(stage/name.lstrip('/'))==digest
 (stage/'usr/share/doc/linux-kernel/README.Fuse.Toddy').write_text('Same frozen Linux7.1.8 source with FUSE_FS=m only. All20previous modules unchanged. New FUSE module/native BIOS+UEFI diagnostic UID101 device/denial/unload and Landlock/seccomp/namespaces passed. Prior boot artifacts retained with -pre-fuse suffix, original foundation rollback and archives retained. Userspace filesystem/helper/installed-system recovery and final image acceptance are separate gates.\n')
 destination.mkdir();subprocess.run(['mount','--bind',str(stage),str(destination)],check=True)
 state.update(state='building-native-archive',stage=str(stage),destination=str(destination),backups=backups,old_modules=oldmodules,kernel_sha256=KERNEL,module_sha256=MODULE);save()
 subprocess.run(['python3',str(R/'scripts/build/stage_package.py'),'linux-kernel',NEW,str(destination),'--source','linux-7.1.8.tar.xz','--recipe','scripts/build/phase2/linux-kernel-fuse-package.sh','--depends','kmod, filesystem-layout','--compression-threads','2'],cwd=R,check=True)
 state.update(state='archive-prepared',archive_sha256=sha(archive(NEW)));save()

def check_archive():
 r=record(NEW);assert not r['installed'] and sha(archive(NEW))==r['archive_sha256']
 assert native('dpkg-query','-W','-f=${Version}','linux-kernel').stdout==OLD
 expected=r['payload'];seen={};process=subprocess.Popen(['dpkg-deb','--fsys-tarfile',str(archive(NEW))],stdout=subprocess.PIPE)
 with tarfile.open(fileobj=process.stdout,mode='r|') as t:
  for m in t:
   name='/'+m.name.removeprefix('./').rstrip('/')
   if name in ['/.','/']:assert m.uid==m.gid==0;continue
   assert name in expected and name not in seen,name
   row=expected[name];assert m.uid==row['uid']==0 and m.gid==row['gid']==0 and m.mode==(row['mode']&0o7777),name
   if m.isfile():value=hashlib.file_digest(t.extractfile(m),'sha256').hexdigest();assert value==row['sha256'],name
   elif m.islnk():value=seen['/'+m.linkname.removeprefix('./')];assert value==row['sha256'],name
   elif m.issym():assert m.linkname==row['symlink'];value=m.linkname
   else:assert m.isdir() and row['directory'];value=True
   seen[name]=value
 assert process.wait()==0 and set(seen)==set(expected)
 stage=json.loads((L/'kernel-fuse-package-prepared-1.json').read_text());assert stage['state']=='archive-prepared'
 for name,digest in {**stage['backups'],**stage['old_modules']}.items():assert expected[name]['sha256']==digest
 assert expected['/boot/vmlinuz-7.1.8-toddy']['sha256']==KERNEL and expected['/usr/lib/modules/7.1.8-toddy/kernel/fs/fuse/fuse.ko']['sha256']==MODULE
 owned(T,record(OLD))
 p=L/'kernel-fuse-archive-verified-1.json';assert not p.exists();p.write_text(json.dumps({'scope':'Full native archive payload/owner/mode/hash and rollback/old modules verified; no install','archive_sha256':r['archive_sha256'],'payload_entries':len(expected),'old_modules_unchanged':20,'backups':stage['backups']},indent=2)+'\n')

def update_boot_config():
 oldversion='0.1-2+toddy1';newversion='0.1-2+toddy2'
 assert native('dpkg-query','-W','-f=${Version}','linux-kernel').stdout==NEW
 assert native('dpkg-query','-W','-f=${Version}','toddy-boot-config').stdout==oldversion
 oldpath=P/('toddy-boot-config_'+oldversion+'_all.json');old=json.loads(oldpath.read_text());assert old['installed'];owned(T,old)
 oldarchive=C/('toddy-boot-config_'+oldversion+'_all.deb');assert sha(oldarchive)==old['archive_sha256']
 stage=T/'sources/stage/phase2-boot-config-fuse';receipt=L/'boot-config-fuse-update-1.json'
 assert not stage.exists() and not receipt.exists(),'Inspect boot-config native metadata/payload before any replay'
 receipt.write_text(json.dumps({'state':'update-intended','old_version':oldversion,'new_version':newversion,'scope':'Exact current boot payload retained; owned dependency metadata follows qualified kernel revision only. No menu/bootloader binary/recovery entry mutation.'})+'\n')
 stage.mkdir();subprocess.run(['dpkg-deb','--extract',str(oldarchive),str(stage)],check=True);owned(stage,old)
 conffiles=native('dpkg-query','-W','-f=${Conffiles}','toddy-boot-config').stdout
 assert {line.split()[0] for line in conffiles.splitlines() if line.strip()}=={'/etc/toddy/grub.cfg'}
 subprocess.run(['python3',str(R/'scripts/build/stage_package.py'),'toddy-boot-config',newversion,str(stage),'--architecture','all','--depends','grub, linux-kernel (= '+NEW+')','--conffile','/etc/toddy/grub.cfg','--recipe','scripts/build/phase2/boot-config-fuse-update.sh','--install'],cwd=R,check=True)
 new=json.loads((P/('toddy-boot-config_'+newversion+'_all.json')).read_text());assert new['installed']
 assert new['payload']==old['payload'],'Metadata update unexpectedly changed boot payload'
 owned(T,new);receipt.write_text(json.dumps({'state':'complete','old_version':oldversion,'new_version':newversion,'archive_sha256':new['archive_sha256'],'owned_payload_unchanged':True,'payload_entries':len(new['payload']),'exact_kernel_dependency':NEW,'scope':'Owned boot metadata dependency only; existing menu/config/recovery bytes unchanged. No installed-system/recovery boot acceptance.'},indent=2)+'\n')

def install():
 passed=json.loads(Path('/var/log/toddy/build/b02-linux-kernel-fuse-package.success.json').read_text());assert passed['recipe_exit']==passed['postcheck_exit']==0
 r=record(NEW);qa=json.loads((L/'kernel-fuse-archive-verified-1.json').read_text());assert not r['installed'] and sha(archive(NEW))==r['archive_sha256']==qa['archive_sha256']
 assert native('dpkg-query','-W','-f=${Version}','linux-kernel').stdout==OLD;owned(T,record(OLD))
 reverse=native('dpkg-query','-W','-f=${Package}\t${Depends}\n').stdout
 exact=[line.split(chr(9))[0] for line in reverse.splitlines() if 'linux-kernel (= '+OLD+')' in line]
 assert exact==['toddy-boot-config'],exact
 assert shutil.disk_usage(T).free>=16*1024**3+archive(NEW).stat().st_size+160*1024**2
 p=L/'kernel-fuse-native-commit-1.json';assert not p.exists(),'Inspect actual package/receipt; never replay uncertain commit'
 p.write_text(json.dumps({'state':'install-intended','archive_sha256':r['archive_sha256']})+'\n')
 PackageBackend(T).install(archive(NEW))
 r['installed']=True;record_path=P/('linux-kernel_'+NEW+'_amd64.json');part=record_path.with_suffix('.part');part.write_text(json.dumps(r,indent=2)+'\n');part.replace(record_path)
 update_boot_config()
 p.write_text(json.dumps({'state':'installed-postcheck-pending','archive_sha256':r['archive_sha256']})+'\n')

def check_installed():
 r=record(NEW);assert r['installed'] and native('dpkg-query','-W','-f=${Version}','linux-kernel').stdout==NEW;owned(T,r)
 assert sha(T/'boot/vmlinuz-7.1.8-toddy')==KERNEL
 stage=json.loads((L/'kernel-fuse-package-prepared-1.json').read_text())
 for name,digest in {**stage['backups'],**stage['old_modules']}.items():assert sha(T/name.lstrip('/'))==digest
 vermagic=native('modinfo','-k','7.1.8-toddy','-F','vermagic','fuse').stdout.strip();assert vermagic.startswith('7.1.8-toddy ')
 alias=native('modprobe','-S','7.1.8-toddy','-R','char-major-10-229').stdout.strip();assert alias=='fuse'
 dependencies=native('modprobe','-S','7.1.8-toddy','--show-depends','fuse').stdout;assert dependencies.strip().endswith('/kernel/fs/fuse/fuse.ko')
 native('apt-get','check');assert not native('dpkg','--audit').stdout.strip()
 assert shutil.disk_usage(T).free>=16*1024**3 and shutil.disk_usage(W).free>=128*1024**2
 p=L/'kernel-fuse-installed-check-1.json';assert not p.exists();p.write_text(json.dumps({'scope':'Owned installed native kernel payload/recovery/module hashes, actual Kmod vermagic/udev alias/dependency lookup and APT; actual installed-system boot/user mount acceptance remains pending.','version':NEW,'archive_sha256':r['archive_sha256'],'kernel_sha256':KERNEL,'payload_entries':len(r['payload']),'module_vermagic':vermagic,'udev_alias':alias,'module_lookup':dependencies,'old_modules_unchanged':20,'target_free':shutil.disk_usage(T).free},indent=2)+'\n')

if __name__=='__main__':
 assert os.getuid()==0 and len(sys.argv)==2
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 {'prepare':prepare,'check-archive':check_archive,'install':install,'check-installed':check_installed,'boot-config':update_boot_config}[sys.argv[1]]()
