"""Native-kernel companion image conversion with owned default-path core/loaders."""
import base64,ctypes,hashlib,json,os,re,subprocess,tempfile,zlib
from pathlib import Path
CONSUMER_SOURCE = None
ACCEPTED_FIXTURE = None

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def output(args):return subprocess.check_output(args,text=True,timeout=15).strip()
def main():
 assert os.geteuid()==0 and os.uname().release=='7.1.8-toddy' and Path('/proc/1/comm').read_text().strip()=='systemd'
 assert output(['systemd-detect-virt','--vm']) in ['kvm','qemu']
 device=output(['findmnt','-n','-o','SOURCE','/']);assert re.fullmatch('/dev/[a-z0-9]+',device)
 parent=output(['lsblk','-ndo','PKNAME',device]);assert re.fullmatch('[a-z0-9]+',parent)
 assert output(['lsblk','-dnro','SERIAL','/dev/'+parent])=='TODDY-BOOT-TEST'
 assert output(['blkid','-s','LABEL','-o','value',device])=='TODDY_LFS'
 assert isinstance(ACCEPTED_FIXTURE,dict) and ACCEPTED_FIXTURE['state']=='complete'
 fixture=Path('/sources/phase2/native-fixtures/glycin-gtk4-1');assert fixture.stat().st_uid==0 and not fixture.is_symlink()
 for name,sha in ACCEPTED_FIXTURE['stage_sha256'].items():assert digest(fixture/'stage'/name)==sha
 for name,sha in ACCEPTED_FIXTURE['installed_core_sha256'].items():assert digest(Path(name))==sha
 assert output(['dpkg-query','-W','-f=${Status} ${Version}','glycin'])=='install ok installed 2.1.5-1+toddy1'
 assert isinstance(CONSUMER_SOURCE,str) and CONSUMER_SOURCE
 def nnp():
  assert os.geteuid()==101 and os.getegid()==101
  assert ctypes.CDLL(None,use_errno=True).prctl(38,1,0,0,0)==0
 with tempfile.TemporaryDirectory(prefix='toddy-glycin-gtk4-') as tmp:
  tmp=Path(tmp);os.chown(tmp,101,101)
  env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':str(tmp),'XDG_CACHE_HOME':str(tmp/'cache'),'PYTHONDONTWRITEBYTECODE':'1','GI_TYPELIB_PATH':str(fixture/'stage/usr/lib/girepository-1.0'),'LD_LIBRARY_PATH':str(fixture/'stage/usr/lib'),'RUST_LOG':'warn'}
  try:
   r=subprocess.run(['python3','-B','-c',CONSUMER_SOURCE],env=env,cwd=tmp,user=101,group=101,extra_groups=[],preexec_fn=nnp,capture_output=True,text=True,timeout=60)
   row={'name':'native-GlyGtk4-bwrap-texture-roundtrip','exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
  except subprocess.TimeoutExpired as e:
   def text(x):return x.decode(errors='replace') if isinstance(x,bytes) else (x or '')
   row={'name':'native-GlyGtk4-bwrap-texture-roundtrip','exit':None,'timeout_seconds':60,'stdout':text(e.stdout),'stderr':text(e.stderr)}
 for name,sha in ACCEPTED_FIXTURE['stage_sha256'].items():assert digest(fixture/'stage'/name)==sha
 for name,sha in ACCEPTED_FIXTURE['installed_core_sha256'].items():assert digest(Path(name))==sha
 raw=json.dumps({'scope':'Native7.1.8 BWRAP image/GdkTexture pixel roundtrip using staged GTK4 companion and owned installed default-path core/loaders. No actual display/widgets/GNOME/physical acceptance.','kernel':os.uname().release,'pid1':'systemd','runs':[row],'stage_file_hashes':ACCEPTED_FIXTURE['stage_sha256'],'installed_core_files_unchanged':ACCEPTED_FIXTURE['installed_core_sha256']},sort_keys=True).encode()
 encoded=base64.b64encode(zlib.compress(raw,9)).decode();chunks=[encoded[i:i+1024] for i in range(0,len(encoded),1024)]
 for i,chunk in enumerate(chunks):print('TODDY_B02_RUNTIME_DATA',i,chunk,flush=True)
 success=row['exit']==0
 print('TODDY_B02_RUNTIME_RESULT',json.dumps({'kernel':os.uname().release,'all_selected_exits_zero':success,'report_sha256':hashlib.sha256(raw).hexdigest(),'chunks':len(chunks)}),flush=True)
 assert success,'Actual native failure retained'
if __name__=='__main__':
 try:main()
 except Exception as error:
  print('TODDY_B02_RUNTIME_FAIL',type(error).__name__,str(error),flush=True)
  raise
