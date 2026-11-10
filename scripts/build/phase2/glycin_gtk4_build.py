"""Build only the frozen GTK4 companion against owned core; image runtime is separate."""
from pathlib import Path
import hashlib,json,os,signal,subprocess,time

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 assert os.getuid()==101
 w=Path('/build');assert not (w/'compile').exists() and not list(Path('/stage').iterdir())
 source=Path('/src/project');lock=digest(source/'Cargo.lock')
 tools=w/'tools';tools.mkdir();wrapper=tools/'cargo'
 wrapper.write_text('''#!/usr/bin/python3
import os,sys
args=sys.argv[1:]
if args and args[0] in ['build','test','metadata']:args=[args[0],'--locked','--offline',*args[1:]]
os.execv('/usr/bin/cargo',['cargo',*args])
''');wrapper.chmod(0o755)
 env=dict(os.environ,PATH=str(tools)+':/usr/bin:/usr/sbin',CARGO_NET_OFFLINE='true',CARGO_BUILD_JOBS='2',RUSTFLAGS='-Cdebuginfo=0',CARGO_INCREMENTAL='0',PYTHONDONTWRITEBYTECODE='1')
 def run(name,command):
  with (w/(name+'.log')).open('xb') as out:
   r=subprocess.Popen(command,env=env,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
   while r.poll() is None:
    fs=os.statvfs(w)
    if fs.f_bavail*fs.f_frsize<128*1024**2:
     assert os.getpgid(r.pid)==r.pid
     os.killpg(r.pid,signal.SIGTERM);r.wait(timeout=30)
     (w/'capacity-refused.json').write_text(json.dumps({'step':name,'minimum_free_bytes':128*1024**2,'actual_free_bytes':fs.f_bavail*fs.f_frsize,'result':'own compiler process group stopped; no promotion'})+'\n')
     raise RuntimeError('Companion scratch reserve reached; preserve outputs, no promotion')
    time.sleep(2)
  (w/(name+'.exit')).write_text(str(r.returncode)+'\n');assert r.returncode==0,(name,r.returncode)
 assert subprocess.check_output(['pkg-config','--modversion','glycin-2'],env=env,text=True).strip()=='2.1.0'
 run('configure',['meson','setup',str(w/'compile'),str(source),'--prefix=/usr','--libdir=lib','--buildtype=release','--wrap-mode=nofallback','-Dprofile=release','-Dlto=false','-Dlibglycin=false','-Dlibglycin-gtk4=true','-Dglycin-loaders=false','-Dglycin-thumbnailer=false','-Dintrospection=true','-Dvapi=false','-Dcapi_docs=false','-Dtests=false','-Dpython_tests=false'])
 home=w/'compile/cargo-home';home.mkdir(exist_ok=True);(home/'config.toml').write_bytes(Path('/src/toddy-cargo.toml').read_bytes())
 run('compile',['ninja','-C',str(w/'compile'),'-j2'])
 assert digest(source/'Cargo.lock')==lock
 run('stage',['meson','install','-C',str(w/'compile'),'--no-rebuild','--destdir','/stage'])
 env.update(GI_TYPELIB_PATH='/stage/usr/lib/girepository-1.0',LD_LIBRARY_PATH='/stage/usr/lib',PKG_CONFIG_PATH='/stage/usr/lib/pkgconfig')
 assert subprocess.check_output(['pkg-config','--modversion','glycin-gtk4-2'],env=env,text=True).strip()=='2.1.0'
 run('GI-symbols',['python3','-c',"import gi,ctypes;gi.require_version('Gly','2');gi.require_version('GlyGtk4','2');from gi.repository import Gly,GlyGtk4;assert callable(GlyGtk4.frame_get_texture);lib=ctypes.CDLL('/stage/usr/lib/libglycin-gtk4-2.so.0');assert lib.gly_gtk_frame_get_texture;assert lib.gly_frame_get_width"])
 r={'scope':'Only GTK4 companion compiled/staged and GI/shared symbols resolved against installed core. No image/frame/texture conversion or upstream Python test execution yet. Core/loaders NOT rebuilt or restaged; no native transaction.','bundle_version':'2.1.5','API_version':'2.1.0','cargo_lock_sha256':lock,'compile_exit':0,'stage_exit':0,'GI_symbol_exit':0,'image_conversion_tested':False,'upstream_tests_passed':0,'package_promotable':False,'artifacts':{str(p.relative_to(w/'compile')):digest(p) for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(p.relative_to('/stage')):digest(p) for p in Path('/stage').rglob('*') if p.is_file() and not p.is_symlink()}}
 (w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ('artifacts','stage_sha256')}))
