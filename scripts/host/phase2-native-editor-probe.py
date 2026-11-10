"""Real installed editor under native-kernel Mutter, test-only GTK instrumentation."""
import base64,ctypes,hashlib,json,os,re,resource,subprocess,tempfile,termios,time,zlib
from pathlib import Path
ACCEPTED = None

def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def output(args):return subprocess.check_output(args,text=True,timeout=15).strip()
def emit(report):
 raw=json.dumps(report,sort_keys=True).encode();assert len(raw)<=4*1024**2
 encoded=base64.b64encode(zlib.compress(raw,9)).decode();chunks=[encoded[i:i+1024] for i in range(0,len(encoded),1024)]
 ok=bool(report.get('all_selected_exits_zero'));fd=os.open('/dev/ttyS1',os.O_WRONLY|os.O_NOCTTY)
 attrs=termios.tcgetattr(fd);attrs[0]=attrs[1]=attrs[3]=0;attrs[2]|=termios.CLOCAL|termios.CREAD;attrs[4]=attrs[5]=termios.B115200;termios.tcsetattr(fd,termios.TCSANOW,attrs)
 with os.fdopen(fd,'w',buffering=1) as evidence:
  for i,chunk in enumerate(chunks):print('TODDY_B02_RUNTIME_DATA',i,chunk,file=evidence,flush=True)
  print('TODDY_B02_RUNTIME_RESULT',json.dumps({'kernel':os.uname().release,'all_selected_exits_zero':ok,'report_sha256':hashlib.sha256(raw).hexdigest(),'chunks':len(chunks)}),file=evidence,flush=True);termios.tcdrain(evidence.fileno())
 assert ok,'Actual editor graphical failure retained'
def main():
 assert os.getuid()==0 and os.uname().release.startswith('7.1.8') and Path('/proc/1/comm').read_text().strip()=='systemd'
 resource.setrlimit(resource.RLIMIT_CORE,(0,0));device=output(['findmnt','-n','-o','SOURCE','/']);parent=output(['lsblk','-ndo','PKNAME',device]);assert output(['lsblk','-dnro','SERIAL','/dev/'+parent])=='TODDY-BOOT-TEST'
 reference=ACCEPTED;assert isinstance(reference,dict)
 manifest=Path(reference['manifest']);assert re.fullmatch(r'/sources/phase2/native-fixtures/editor-[12]/accepted[.]json',str(manifest)) and not manifest.is_symlink() and manifest.stat().st_uid==0 and not manifest.stat().st_mode&0o222
 assert manifest.stat().st_size<512*1024 and sha(manifest)==reference['manifest_sha256']
 accepted=json.loads(manifest.read_text())
 for path,digest in accepted['artifacts'].items():assert sha(Path(path))==digest
 library=Path(accepted['driver_library']);script=Path(accepted['session_script'])
 assert sha(library)==accepted['driver_sha256'] and sha(script)==accepted['session_script_sha256']
 report={'scope':'Actual installed unmodified GNOME Text Editor50.1 in native kernel/Systemd, headless Mutter/Wayland. Test-only GTK instrumentation, real mapped active window/text editing/save/normal reopen/resize and client renderer PNGs. Not physical input, full GNOME/login, crash recovery or hardware acceptance.','kernel':os.uname().release,'pid1':'systemd','uid':101,'runs':[],'all_selected_exits_zero':False}
 def nnp():
  assert ctypes.CDLL(None,use_errno=True).prctl(38,1,0,0,0)==0
  status=Path('/proc/self/status').read_text();assert 'NoNewPrivs:\t1' in status and 'CapEff:\t0000000000000000' in status
 with tempfile.TemporaryDirectory(prefix='toddy-editor-native-',dir='/tmp') as directory:
  root=Path(directory);os.chown(root,101,101);runtime=root/'runtime';runtime.mkdir(mode=0o700);os.chown(runtime,101,101)
  env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':str(root),'XDG_RUNTIME_DIR':str(runtime),'XDG_CACHE_HOME':str(root/'cache'),'XDG_CONFIG_HOME':str(root/'config'),'XDG_DATA_HOME':str(root/'data'),'XDG_SESSION_TYPE':'wayland','XDG_CURRENT_DESKTOP':'GNOME','LIBGL_ALWAYS_SOFTWARE':'1','GALLIUM_DRIVER':'llvmpipe','GDK_DISABLE':'vulkan','PYTHONDONTWRITEBYTECODE':'1'}
  args=['dbus-run-session','--','mutter','--wayland','--headless','--virtual-monitor=1280x720','--wayland-display=toddy-editor-proof','--','python3','-B',str(script),str(root),str(library),accepted['driver_sha256']]
  started=time.monotonic()
  try:
   with (root/'compositor.log').open('xb') as out:r=subprocess.run(args,env=env,cwd=root,user=101,group=101,extra_groups=[],preexec_fn=nnp,stdout=out,stderr=subprocess.STDOUT,timeout=170)
   report['compositor_exit']=r.returncode
  except subprocess.TimeoutExpired:report['compositor_exit']=None;report['timeout_seconds']=170
  report['elapsed_seconds']=round(time.monotonic()-started,3);report['compositor_log']=(root/'compositor.log').read_text(errors='replace')
  result=root/'suite-result.json'
  if result.exists():
   suite=json.loads(result.read_text());report['suite']=suite;report['runs']=suite['runs'];report['all_selected_exits_zero']=report['compositor_exit']==0 and suite['all_selected_exits_zero'] is True
  else:report['runs']=[{'name':'native-editor-suite','exit':report['compositor_exit'],'missing_suite_result':True}]
  images=[]
  for p in sorted(root.glob('gtk-editor-*.png')):
   data=p.read_bytes();assert data.startswith(b'\x89PNG\r\n\x1a\n') and len(data)<2*1024**2
   images.append({'name':p.name,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'png_base64':base64.b64encode(data).decode()})
  report['native_client_images']=images
  for path,digest in accepted['artifacts'].items():assert sha(Path(path))==digest
  assert sha(library)==accepted['driver_sha256'] and sha(script)==accepted['session_script_sha256']
  report['artifacts_unchanged']=len(accepted['artifacts'])+2
  emit(report)
if __name__=='__main__':
 try:main()
 except Exception as error:print('TODDY_B02_RUNTIME_FAIL',type(error).__name__,str(error),flush=True);raise
