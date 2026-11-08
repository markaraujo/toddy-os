"""Native SVG renderer build/tests/stage with frozen offline Rust sources."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess


def main():
    assert os.getuid()==101 and not Path('/build/source').exists() and not list(Path('/stage').iterdir())
    def free():
        fs=os.statvfs('/build');return fs.f_bavail*fs.f_frsize
    assert free()>=18*1024**3
    shutil.copytree('/src/project','/build/source',symlinks=True)
    home=Path('/build/cargo-home');home.mkdir()
    (home/'config.toml').write_bytes(Path('/src/toddy-cargo.toml').read_bytes())
    env=dict(os.environ,CARGO_HOME=str(home),CARGO_NET_OFFLINE='true',CARGO_BUILD_JOBS='4',
             CARGO_PROFILE_RELEASE_DEBUG='0',CARGO_PROFILE_TEST_DEBUG='0',CARGO_INCREMENTAL='0')
    phases=[]
    def run(name,command,extra=None):
        with Path('/build/'+name+'.log').open('xb') as output:
            process=subprocess.Popen(command,cwd='/build',env=dict(env,**(extra or {})),stdout=output,
                                     stderr=subprocess.STDOUT,start_new_session=True)
            reserve_stop=False
            while True:
                try:code=process.wait(timeout=10);break
                except subprocess.TimeoutExpired:
                    if free()<16*1024**3:
                        reserve_stop=True;os.killpg(process.pid,signal.SIGTERM)
                        try:code=process.wait(timeout=15)
                        except subprocess.TimeoutExpired:
                            os.killpg(process.pid,signal.SIGKILL);code=process.wait()
                        break
        Path('/build/'+name+'.exit').write_text(str(code)+'\n')
        result={'phase':name,'native_exit':code,'command':command,'reserve_stop':reserve_stop,
                'free_bytes':free(),'log_sha256':hashlib.sha256(Path('/build/'+name+'.log').read_bytes()).hexdigest()}
        phases.append(result);Path('/build/phases.json').write_text(json.dumps(phases,indent=2)+'\n')
        print(json.dumps(result),flush=True)
        assert code==0 and not reserve_stop,name+' failed; preserve outputs and inspect'
        assert free()>=16*1024**3
    run('configure',['meson','setup','/build/compile','/build/source','--prefix=/usr','--libdir=lib',
        '--buildtype=release','--wrap-mode=nofallback','-Ddefault_library=shared','-Db_lto=false',
        '-Davif=disabled','-Dpixbuf=enabled','-Dpixbuf-loader=enabled','-Drsvg-convert=enabled',
        '-Dintrospection=enabled','-Dtests=true','-Ddocs=disabled','-Dvala=disabled'])
    run('build',['ninja','-C','/build/compile','-j4'])
    run('upstream-tests',['meson','test','-C','/build/compile','--print-errorlogs','--num-processes','1'])
    run('stage',['ninja','-C','/build/compile','install'],{'DESTDIR':'/stage'})
    modules=list(Path('/stage/usr/lib/gdk-pixbuf-2.0/2.10.0/loaders').glob('*.so'))
    assert len(modules)==1 and modules[0].name=='libpixbufloader_svg.so'
    run('loader-query',['gdk-pixbuf-query-loaders',str(modules[0])],{'LD_LIBRARY_PATH':'/stage/usr/lib'})
    cache=Path('/build/loader-query.log');text=cache.read_text()
    assert '"svg"' in text and str(modules[0]) in text
    flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','librsvg-2.0','gdk-pixbuf-2.0'],
         env=dict(env,PKG_CONFIG_PATH='/stage/usr/lib/pkgconfig'),text=True))
    run('consumer-compile',['cc','-Wall','-Wextra','-Werror','/src/toddy-probe.c',
         '-I/stage/usr/include/librsvg-2.0','-L/stage/usr/lib',*flags,'-o','/build/svg-consumer'])
    run('consumer',['/build/svg-consumer'],{'LD_LIBRARY_PATH':'/stage/usr/lib','GDK_PIXBUF_MODULE_FILE':str(cache)})
    rows=[json.loads(line) for line in Path('/build/compile/meson-logs/testlog.json').read_text().splitlines()]
    assert rows and all(r['result']=='OK' and r['returncode']==0 for r in rows)
    Path('/build/test-results.json').write_text(json.dumps({'scope':'Actual native upstream SVG tests, Cairo pixel/malformed SVG refusal and Gdk loader; no window/session acceptance',
         'registered_tests':len(rows),'tests':[{'name':r['name'],'result':r['result'],'returncode':r['returncode']} for r in rows],
         'phases':phases,'consumer_stdout':Path('/build/consumer.log').read_text(),'staged_consumer_exit':0,
         'generated_cache_scope':'Private staged-module paths for probe only; installed cache requires controlled owned update',
         'free_bytes_after_build':free()},indent=2)+'\n')


if __name__=='__main__':main()
