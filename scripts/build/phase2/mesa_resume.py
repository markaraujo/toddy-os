"""Build only missing test tools, reuse43 passes, finish first stage/pixel proof."""
import hashlib
import json
import os
from pathlib import Path
import subprocess


def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    assert os.getuid()==101
    root=Path('/build');build=root/'compile';recovery=root/'mesa-recovery-2'
    assert not recovery.exists() and not list(Path('/stage').iterdir()) and not (root/'test-results.json').exists()
    rows=[json.loads(line) for line in (build/'meson-logs/testlog.json').read_text().splitlines()]
    failed=[r for r in rows if r['result']!='OK']
    names={'glcpp test (unix)','glcpp test (windows)','glcpp test (oldmac)','glcpp test (bizarro)','glsl compiler warnings'}
    assert len(rows)==48 and len(failed)==5 and {r['name'].rsplit(':',1)[1] for r in failed}==names
    assert all(r['returncode']==1 and 'FileNotFoundError' in r['stderr'] for r in failed)
    assert all(r['returncode']==0 for r in rows if r['result']=='OK')
    before=json.loads((root/'compiled-binaries.json').read_text())
    assert before and all(digest(root/p)==sha for p,sha in before.items())
    targets=['src/compiler/glsl/glcpp/glcpp','src/compiler/glsl/glsl_compiler']
    assert all(not (build/p).exists() for p in targets)
    recovery.mkdir()
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',XDG_CACHE_HOME='/build/cache')

    def run(name,command,extra=None):
        with (recovery/(name+'.log')).open('xb') as out:
            result=subprocess.run(command,cwd=build,env=dict(env,**(extra or {})),stdout=out,stderr=subprocess.STDOUT)
        (recovery/(name+'.exit')).write_text(str(result.returncode)+'\n')
        assert result.returncode==0,name+' failed; preserve prior results'

    run('missing-test-tools',['ninja','-C',str(build),'-j4',*targets])
    assert all((build/p).is_file() for p in targets)
    assert all(digest(root/p)==sha for p,sha in before.items()),'Prior compiled outputs changed'
    run('affected-tests',['meson','test','-C',str(build),'--no-rebuild','--print-errorlogs',
                          '--num-processes','4','--timeout-multiplier','4','--logbase','testlog-recovery-2',*sorted(names)])
    corrected_path=build/'meson-logs/testlog-recovery-2.json'
    corrected=[json.loads(line) for line in corrected_path.read_text().splitlines()]
    assert len(corrected)==5 and all(r['result']=='OK' and r['returncode']==0 for r in corrected)
    assert {r['name'] for r in corrected}=={r['name'] for r in failed}
    run('first-stage',['ninja','-C',str(build),'install'],{'DESTDIR':'/stage'})
    flags=subprocess.check_output(['pkg-config','--cflags','--libs','egl','glesv2'],
                                  env=dict(env,PKG_CONFIG_PATH='/stage/usr/lib/pkgconfig'),text=True).split()
    run('consumer-compile',['cc','-Wall','-Wextra','-Werror','/src/toddy-probe.c',
                            '-I/stage/usr/include','-L/stage/usr/lib',*flags,'-o','/build/mesa-consumer'])
    with (root/'native-render.log').open('xb') as out:
        result=subprocess.run(['/build/mesa-consumer'],env=dict(env,LD_LIBRARY_PATH='/stage/usr/lib',
                              LIBGL_DRIVERS_PATH='/stage/usr/lib/dri',LIBGL_ALWAYS_SOFTWARE='1',
                              GALLIUM_DRIVER='llvmpipe',EGL_PLATFORM='surfaceless'),stdout=out,stderr=subprocess.STDOUT)
    (recovery/'render.exit').write_text(str(result.returncode)+'\n')
    assert result.returncode==0,'Native staged renderer failed'
    text=(root/'native-render.log').read_text();assert 'renderer: llvmpipe' in text
    pixel=[int(v) for line in text.splitlines() if line.startswith('pixel: ') for v in line.removeprefix('pixel: ').split()]
    assert len(pixel)==4 and pixel[0]==0 and abs(pixel[1]-32)<=1 and abs(pixel[2]-64)<=1 and pixel[3]==255
    assert all(digest(root/p)==sha for p,sha in before.items()),'Prior compiled outputs changed'
    merged={r['name']:{'name':r['name'],'result':r['result'],'returncode':r['returncode']} for r in rows}
    for r in corrected:merged[r['name']]={k:r[k] for k in ['name','result','returncode']}
    assert len(merged)==48 and all(r['result']=='OK' and r['returncode']==0 for r in merged.values())
    fs=os.statvfs('/build');assert fs.f_bavail*fs.f_frsize>=16*1024**3
    proof={'scope':'Reference software/virtual Wayland EGL/GBM profile, native CPU shader/raster/pixel proof; not GNOME/window/hardware acceptance',
        'registered_tests':48,'tests':list(merged.values()),'original_wrapper_exit':1,
        'original_tests':{'passed':43,'failed':5,'log_sha256':digest(build/'meson-logs/testlog.json')},
        'affected_recheck':{'passed':5,'failed':0,'log_sha256':digest(corrected_path)},
        'upstream_log_sha256':digest(build/'meson-logs/testlog.json'),
        'consumer_exit':0,'native_render_stdout':text,'native_render_sha256':digest(root/'native-render.log'),
        'unchanged_compiled_elfs':len(before),'free_bytes_after_build':fs.f_bavail*fs.f_frsize,
        'recovery':'Only two build_by_default:false test dependencies added, five failed wrappers rechecked; original43passes and all original compiled ELFs retained unchanged. Original failed log/exit preserved.'}
    (root/'test-results.json').write_text(json.dumps(proof,indent=2)+'\n')


if __name__=='__main__':main()
