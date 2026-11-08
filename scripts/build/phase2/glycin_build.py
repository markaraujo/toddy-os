"""Compile the frozen core/two loaders offline; native image qualification is separate."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess


def main():
    assert os.getuid()==101 and not list(Path('/stage').iterdir())
    work=Path('/build');source=Path('/src/project')
    volume=json.loads((Path('/src')/'toddy-prepared.json').read_text())['work_volume']
    assert volume['size_bytes']==2560*1024**2
    tools=work/'tools';tools.mkdir()
    wrapper=tools/'cargo';wrapper.write_text('''#!/usr/bin/python3
import os,sys
args=sys.argv[1:]
if args and args[0] in ['build','test','metadata']:
 args=[args[0],'--locked','--offline',*args[1:]]
os.execv('/usr/bin/cargo',['cargo',*args])
''');wrapper.chmod(0o755)
    env=dict(os.environ,PATH=str(tools)+':/usr/bin:/usr/sbin',CARGO_NET_OFFLINE='true',CARGO_BUILD_JOBS='2',
             RUSTFLAGS='-Cdebuginfo=0',CARGO_INCREMENTAL='0')
    for name in ['bwrap','cargo','rustc']:
        result=subprocess.run(['/usr/bin/'+name,'--version'],env=env,text=True,capture_output=True,check=True)
        (work/(name+'-version.log')).write_text(result.stdout+result.stderr)
    compile_dir=work/'compile'
    def run(name,args,**kwargs):
        with (work/(name+'.log')).open('xb') as log:
            r=subprocess.run(args,env=env,stdout=log,stderr=subprocess.STDOUT,**kwargs)
        (work/(name+'.exit')).write_text(str(r.returncode)+'\n');assert r.returncode==0,(name,r.returncode)
    run('configure',['meson','setup',str(compile_dir),str(source),'--prefix=/usr','--libdir=lib','--buildtype=release',
        '--wrap-mode=nofallback','-Dprofile=release','-Dlibglycin=true','-Dlibglycin-gtk4=false',
        '-Dglycin-loaders=true','-Dloaders=glycin-image-rs,glycin-svg','-Dglycin-thumbnailer=false',
        '-Dintrospection=true','-Dvapi=false','-Dcapi_docs=false','-Dtests=true','-Dtest_tokio=false'])
    home=compile_dir/'cargo-home';home.mkdir(exist_ok=True)
    (home/'config.toml').write_bytes(Path('/src/toddy-cargo.toml').read_bytes())
    lock_before=hashlib.sha256((source/'Cargo.lock').read_bytes()).hexdigest()
    run('compile',['ninja','-C',str(compile_dir),'-j2'])
    assert hashlib.sha256((source/'Cargo.lock').read_bytes()).hexdigest()==lock_before
    run('stage',['meson','install','-C',str(compile_dir),'--no-rebuild','--destdir','/stage'])
    env['PKG_CONFIG_PATH']='/stage/usr/lib/pkgconfig'
    api=subprocess.check_output(['pkg-config','--modversion','glycin-2'],env=env,text=True).strip()
    assert api=='2.1.0',api  # Global bundle2.1.5 and libglycin2.1.0 are distinct upstream versions.
    flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','glycin-2'],env=env,text=True))
    run('consumer-build',['cc','-std=c11','-Wall','-Wextra','-Werror','/src/toddy-probe.c','-I/stage/usr/include/glycin-2',
        '-L/stage/usr/lib','-Wl,-rpath,/stage/usr/lib',*flags,'-o',str(work/'native-types')])
    run('consumer',[str(work/'native-types')])
    env.update(GI_TYPELIB_PATH='/stage/usr/lib/girepository-1.0',LD_LIBRARY_PATH='/stage/usr/lib',PYTHONDONTWRITEBYTECODE='1')
    run('gi',['python3','-B','-c',"import gi;gi.require_version('Gly','2');from gi.repository import Gly,GLib;l=Gly.Loader.new_for_bytes(GLib.Bytes.new(b'pending-native-image-test'));assert l is not None;l.set_sandbox_selector(Gly.SandboxSelector.BWRAP)"])
    registered=json.loads((compile_dir/'meson-info/intro-tests.json').read_text())
    assert registered
    result={'scope':'Offline compiled Glycin core/two loaders, staged C/GI type construction only; UNQUALIFIED pending real native sandbox/image/upstream tests',
            'bundle_version':'2.1.5','libglycin_api_version':api,'loaders':['glycin-image-rs','glycin-svg'],
            'cargo_lock_sha256':lock_before,'native_compile_exit':0,'staged_type_constructor_exit':0,'gi_type_constructor_exit':0,
            'upstream_tests_passed':0,'native_runtime_pending':[r['name'] for r in registered],
            'profile':'No HEIF/JXL/raw loader products, thumbnailer/GTK4 companion/Vala/docs; source tests enabled for later native execution, sandbox never disabled',
            'package_promotable':False}
    (work/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
