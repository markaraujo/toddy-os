"""Stage candidate images over the authenticated qualified foundation payload."""
from pathlib import Path
import hashlib,json,os,shutil,stat,subprocess
assert os.getuid()==101
w=Path('/build');s=Path('/stage');assert not list(s.iterdir()) and not (w/'kernel-stage-1.json').exists()
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
archive=Path('/src/toddy-foundation-kernel.deb');record=json.loads(Path('/src/toddy-foundation-kernel.json').read_text())
assert record['name']=='linux-kernel' and record['version']=='7.1.8-1' and record['installed']
assert sha(archive)==record['archive_sha256']=='27d73576eb43dcfccb214b95913a2df2ef46763d25e6d85ef2b10e7118c1ee74'
a=json.loads((w/'kernel-build-4/artifacts.json').read_text())
for name,digest in a.items():assert sha(w/'merged'/name)==digest
assert a['arch/x86/boot/bzImage']=='18c4d9e6a64554296d8e9a037c2383e7426a0cf155b6d757d0693fce0d087ad1'
subprocess.run(['dpkg-deb','--extract',str(archive),str(s)],check=True)
old=record['payload']
for name,row in old.items():
 p=s/name.lstrip('/');st=p.lstat();assert st.st_mode==row['mode'],name
 if 'sha256' in row:assert sha(p)==row['sha256'],name
 elif 'symlink' in row:assert os.readlink(p)==row['symlink'],name
 else:assert row['directory']
assert {('/'+str(p.relative_to(s))) for p in s.rglob('*')}==set(old)
# The feature is built in. All existing modular outputs must remain identical;
# do not replace known module payloads with a different/unqualified module set.
prefix='/usr/lib/modules/7.1.8-toddy/kernel/';modules={}
for name,row in old.items():
 if name.startswith(prefix) and name.endswith('.ko'):
  relative=name.removeprefix(prefix);assert sha(w/'merged'/relative)==row['sha256'];modules[relative]=row['sha256']
assert len(modules)==20
ordered=(w/'merged/modules.order').read_text().splitlines()
assert len(ordered)==20 and all(name.endswith('.o') for name in ordered)
assert {name.removesuffix('.o')+'.ko' for name in ordered}==set(modules)
backups={};images={'vmlinuz':'arch/x86/boot/bzImage','System.map':'System.map','config':'.config'}
for stem,built in images.items():
 p=s/'boot'/(stem+'-7.1.8-toddy');backup=p.with_name(p.name+'-foundation');assert not backup.exists()
 shutil.copyfile(p,backup);backup.chmod(0o644);backups[str(backup.relative_to(s))]=sha(backup)
 shutil.copyfile(w/'merged'/built,p);p.chmod(0o644);assert sha(p)==a[built]
doc=s/'usr/share/doc/linux-kernel/README.Landlock.Toddy';assert not doc.exists()
doc.write_text('Same frozen Linux7.1.8 source/kernelrelease; Landlock and selected SECURITY_PATH enabled. All20 original modules unchanged. Foundation image/config/System.map retained with -foundation suffix. Old archive retained. Boot menu ownership belongs to toddy-boot-config; its recovery entry and installed-system boot remain separate qualification. Actual BIOS/UEFI diagnostic Landlock ABI9/UID101 denial/recovery/seccomp/module/namespaces passed; no full desktop/ISO/hardware claim. ADR0201.\n')
rows={str(p.relative_to(s)):sha(p) for p in s.rglob('*') if p.is_file() and not p.is_symlink()}
free=os.statvfs(w).f_bavail*os.statvfs(w).f_frsize;assert free>=128*1024**2
r={'scope':'UID101 isolated native kernel stage only; authenticated original payload reused, candidate images and three foundation rollback artifacts,20 identical modules. No native install/boot-entry/installed Systemd/desktop acceptance.','stage_exit':0,'foundation_archive_sha256':record['archive_sha256'],'foundation_payload_entries':len(old),'modules':modules,'backups':backups,'candidate_artifacts':a,'stage_sha256':rows,'free_bytes':free}
(w/'kernel-stage-1.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ['stage_sha256','modules']}))
