"""Tecla staged CLI under an actual native Wayland compositor, not a GUI pass."""
import base64,ctypes,hashlib,json,os,re,resource,subprocess,tempfile,termios,time,zlib
from pathlib import Path
ACCEPTED = None

def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def output(args):return subprocess.check_output(args,text=True,timeout=15).strip()
def emit(report):
 raw=json.dumps(report,sort_keys=True).encode();assert len(raw)<4*1024**2
 data=base64.b64encode(zlib.compress(raw,9)).decode();chunks=[data[i:i+1024] for i in range(0,len(data),1024)]
 fd=os.open('/dev/ttyS1',os.O_WRONLY|os.O_NOCTTY);attrs=termios.tcgetattr(fd);attrs[0]=attrs[1]=attrs[3]=0;attrs[2]|=termios.CLOCAL|termios.CREAD;attrs[4]=attrs[5]=termios.B115200;termios.tcsetattr(fd,termios.TCSANOW,attrs)
 with os.fdopen(fd,'w',buffering=1) as out:
  for i,chunk in enumerate(chunks):print('TODDY_B02_RUNTIME_DATA',i,chunk,file=out,flush=True)
  print('TODDY_B02_RUNTIME_RESULT',json.dumps({'kernel':os.uname().release,'all_selected_exits_zero':report['all_selected_exits_zero'],'report_sha256':hashlib.sha256(raw).hexdigest(),'chunks':len(chunks)}),file=out,flush=True);termios.tcdrain(out.fileno())
 assert report['all_selected_exits_zero'],'Actual Tecla CLI failure retained'
def main():
 assert os.getuid()==0 and os.uname().release=='7.1.8-toddy' and Path('/proc/1/comm').read_text().strip()=='systemd'
 resource.setrlimit(resource.RLIMIT_CORE,(0,0));device=output(['findmnt','-n','-o','SOURCE','/']);parent=output(['lsblk','-ndo','PKNAME',device]);assert output(['lsblk','-dnro','SERIAL','/dev/'+parent])=='TODDY-BOOT-TEST'
 ref=ACCEPTED;manifest=Path(ref['manifest']);assert str(manifest)=='/sources/phase2/native-fixtures/tecla-cli-1/accepted.json' and not manifest.is_symlink() and manifest.stat().st_uid==0 and not manifest.stat().st_mode&0o222 and manifest.stat().st_size<512*1024 and sha(manifest)==ref['manifest_sha256']
 accepted=json.loads(manifest.read_text())
 for path,digest in accepted['artifacts'].items():assert sha(Path(path))==digest
 report={'scope':'Native7.1.8/Systemd/Mutter Wayland staged Tecla50.0 --version/--help only, UID101/NoNewPrivs/no external network. Adwaita requires display even for CLI. No graphical keyboard preview/input/GUI/complete GNOME/hardware acceptance.','kernel':os.uname().release,'pid1':'systemd','runs':[],'all_selected_exits_zero':False}
 with tempfile.TemporaryDirectory(prefix='toddy-tecla-native-',dir='/tmp') as directory:
  root=Path(directory);os.chown(root,101,101);runtime=root/'runtime';runtime.mkdir(mode=0o700);os.chown(runtime,101,101)
  suite=r'''from pathlib import Path
import json,os,subprocess,sys
assert os.geteuid()==os.getegid()==101 and 'NoNewPrivs:\t1' in Path('/proc/self/status').read_text()
root=Path(sys.argv[1]);binary=sys.argv[2];rows=[];os.environ['GDK_BACKEND']='wayland'
try:
 for arg in ['--version','--help']:
  r=subprocess.run([binary,arg],text=True,capture_output=True,timeout=20)
  rows.append({'name':'tecla '+arg,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
  assert r.returncode==0
  assert ('tecla 50.0' in r.stdout) if arg=='--version' else ('--version' in r.stdout)
 result={'runs':rows,'all_selected_exits_zero':len(rows)==2,'Wayland_display':os.environ.get('WAYLAND_DISPLAY'),'graphical_preview_tested':False}
except Exception as error:result={'runs':rows,'all_selected_exits_zero':False,'failure':{'type':type(error).__name__,'message':str(error)}}
(root/'cli-result.json').write_text(json.dumps(result,indent=2)+'\n');raise SystemExit(0 if result['all_selected_exits_zero'] else 1)
'''
  script=root/'suite.py';script.write_text(suite);script.chmod(0o644)
  env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':str(root),'XDG_RUNTIME_DIR':str(runtime),'XDG_CACHE_HOME':str(root/'cache'),'XDG_CONFIG_HOME':str(root/'config'),'XDG_DATA_HOME':str(root/'data'),'XDG_SESSION_TYPE':'wayland','XDG_CURRENT_DESKTOP':'GNOME','LIBGL_ALWAYS_SOFTWARE':'1','GALLIUM_DRIVER':'llvmpipe','GDK_DISABLE':'vulkan','PYTHONDONTWRITEBYTECODE':'1'}
  def nnp():assert ctypes.CDLL(None,use_errno=True).prctl(38,1,0,0,0)==0
  args=['dbus-run-session','--','mutter','--wayland','--headless','--virtual-monitor=1280x720','--wayland-display=toddy-tecla-proof','--','python3','-B',str(script),str(root),accepted['binary']]
  try:
   with (root/'compositor.log').open('xb') as log:r=subprocess.run(args,env=env,cwd=root,user=101,group=101,extra_groups=[],preexec_fn=nnp,stdout=log,stderr=subprocess.STDOUT,timeout=80)
   report['compositor_exit']=r.returncode
  except subprocess.TimeoutExpired:report['compositor_exit']=None
  report['compositor_log']=(root/'compositor.log').read_text(errors='replace');result=root/'cli-result.json'
  if result.exists():
   actual=json.loads(result.read_text());report['details']=actual;report['runs']=actual['runs'];report['all_selected_exits_zero']=report['compositor_exit']==0 and actual['all_selected_exits_zero'] is True
  for path,digest in accepted['artifacts'].items():assert sha(Path(path))==digest
  report['artifacts_unchanged']=len(accepted['artifacts']);emit(report)
if __name__=='__main__':
 try:main()
 except Exception as error:print('TODDY_B02_RUNTIME_FAIL',type(error).__name__,str(error),flush=True);raise
