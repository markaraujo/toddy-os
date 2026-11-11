"""Promote verified portal stages through owned native package transactions."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
from verify_stage import inspect_stage
R=Path('/opt/toddy-build');T=Path('/mnt/lfs');L=Path('/var/log/toddy/phase2')
PROFILES={
 'xdg-desktop-portal':('1.22.1','usr/libexec/xdg-desktop-portal',['glib','json-glib','pipewire','systemd','fuse','bubblewrap','gdk-pixbuf','dbus']),
 'xdg-desktop-portal-gnome':('50.0','usr/libexec/xdg-desktop-portal-gnome',['xdg-desktop-portal','libadwaita','gtk','gnome-desktop','gsettings-desktop-schemas','fontconfig']),
 'xdg-desktop-portal-gtk':('1.15.3','usr/libexec/xdg-desktop-portal-gtk',['xdg-desktop-portal','gtk3','gsettings-desktop-schemas','fontconfig'])}
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def query(name,fmt='${Version}'):
 return subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f='+fmt,name],text=True)
def install(name):
 version,binary,deps=PROFILES[name];v=version+'-1+toddy1';w=T/'sources/phase2/work'/(name+'-1');stage=w/'stage'
 assert (L/(name+'-build-1.exit')).read_text().strip()=='0'
 r=json.loads((w/'stage-results.json').read_text());assert r['name']==name and r['version']==version and r['compile_exit']==r['stage_exit']==0
 inspection=inspect_stage(stage)
 assert {str(p.relative_to(stage)):sha(p) for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}==r['stage_sha256']
 assert subprocess.run(['chroot',str(T),'dpkg-query','-W',name],capture_output=True).returncode==1
 destination=T/'sources/stage'/('phase2-'+name);receipt=L/(name+'-native-install-1.json')
 assert not any(os.path.lexists(p) for p in [destination,receipt,receipt.with_suffix('.part')]),'Inspect actual prior promotion/install before resuming'
 assert shutil.disk_usage(T).free>=16*1024**3+128*1024**2
 dependencies=', '.join(n+(' (>= ' if n=='gtk' else ' (= ')+query(n)+')' for n in deps)
 state={'state':'promotion-intended','name':name,'version':v,'source_stage_manifest_sha256':inspection['manifest_sha256'],'depends':dependencies}
 def save():
  p=receipt.with_suffix('.part');p.write_text(json.dumps(state,indent=2)+'\n');p.replace(receipt)
 save();shutil.copytree(stage,destination,symlinks=True)
 doc=destination/'usr/share/doc'/name;doc.mkdir(parents=True,exist_ok=True)
 source=T/'sources/phase2/inputs'/(name+'-'+version)
 shutil.copyfile(source/'COPYING',doc/'copyright')
 (doc/'README.Toddy').write_text('Pinned source-built native portal. Sandboxed image/sound validation remains enabled in the base. Optional upstream integration suite was not run in the frozen-book build profile. Installed CLI/payload checks do not prove actual desktop consent, cancellation, denial or appearance integration; those require a native session. No credentials, model or hosted provider is required.\n')
 state['state']='installing-native-package';save()
 row=next(x for x in json.loads((R/'config/phase2/sources.lock.json').read_text())['components'] if x['name']==name)
 subprocess.run(['python3',str(R/'scripts/build/stage_package.py'),name,v,str(destination),'--source',row['filename'],'--recipe','scripts/build/phase2/'+name+'-install.sh','--depends',dependencies,'--install'],cwd=R,check=True)
 state['state']='installed-postcheck-pending';save()
def check(name):
 version,binary,_=PROFILES[name];v=version+'-1+toddy1'
 assert query(name,'${Status} ${Version}')=='install ok installed '+v
 record=json.loads(Path('/var/log/toddy/packages',name+'_'+v+'_amd64.json').read_text());assert record['installed']
 for path,row in record['payload'].items():
  p=T/path.lstrip('/');s=p.lstat();assert s.st_mode==row['mode'] and s.st_uid==row['uid']==0 and s.st_gid==row['gid']==0,path
  if 'sha256' in row:assert sha(p)==row['sha256'],path
  elif 'symlink' in row:assert os.readlink(p)==row['symlink'],path
  if not p.is_symlink():assert not s.st_mode&0o6000,path
 ldd=subprocess.check_output(['chroot',str(T),'ldd','/'+binary],text=True);assert 'not found' not in ldd
 cli=None
 if name=='xdg-desktop-portal':
  cli=subprocess.run(['setpriv','--no-new-privs','chroot','--userspec=101:101','--groups=101',str(T),'/'+binary,'--version'],capture_output=True,text=True,timeout=15)
  assert cli.returncode==0 and version in cli.stdout
 assert not subprocess.check_output(['chroot',str(T),'dpkg','--audit'],text=True).strip()
 subprocess.run(['chroot',str(T),'apt-get','check'],check=True)
 receipt=L/(name+'-installed-check-1.json');assert not receipt.exists()
 receipt.write_text(json.dumps({'scope':'Owned installed payload, dependency resolution and APT. Native desktop session/consent/cancel/denial/appearance still pending.','name':name,'version':v,'archive_sha256':record['archive_sha256'],'payload_entries':len(record['payload']),'ldd':ldd,'version_cli':cli.stdout.strip() if cli else None},indent=2)+'\n')
if __name__=='__main__':
 assert os.getuid()==0 and len(sys.argv)==3 and sys.argv[2] in PROFILES
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 {'install':install,'check':check}[sys.argv[1]](sys.argv[2])
