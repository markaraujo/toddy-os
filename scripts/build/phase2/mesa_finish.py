"""Finish only staged EGL consumer after link-search correction; no test/install replay."""
import hashlib
import json
import os
from pathlib import Path
import subprocess


def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def entries(root):
    result={}
    for p in sorted(root.rglob('*')):
        relative=str(p.relative_to(root))
        if p.is_symlink():result[relative]={'symlink':os.readlink(p)}
        elif p.is_file():result[relative]={'sha256':digest(p),'size':p.stat().st_size}
    return result


def main():
    assert os.getuid()==101
    root=Path('/build');build=root/'compile';previous=root/'mesa-recovery-2';finish=root/'mesa-finish-3'
    assert not finish.exists() and not (root/'test-results.json').exists() and not (root/'mesa-consumer').exists()
    for label in ['missing-test-tools','affected-tests','first-stage']:
        assert (previous/(label+'.exit')).read_text().strip()=='0'
    assert (previous/'consumer-compile.exit').read_text().strip()=='1'
    old=(previous/'consumer-compile.log').read_text()
    assert 'libgallium-26.1.7.so' in old and 'libgbm.so.1' in old and 'not found (try using -rpath or -rpath-link)' in old
    original=[json.loads(line) for line in (build/'meson-logs/testlog.json').read_text().splitlines()]
    corrected_path=build/'meson-logs/testlog-recovery-2.json'
    corrected=[json.loads(line) for line in corrected_path.read_text().splitlines()]
    failed=[r for r in original if r['result']!='OK']
    assert len(original)==48 and len(failed)==5 and len(corrected)==5
    assert all(r['result']=='OK' and r['returncode']==0 for r in corrected)
    assert all(r['returncode']==0 for r in original if r['result']=='OK')
    assert {r['name'] for r in failed}=={r['name'] for r in corrected}
    before=json.loads((root/'compiled-binaries.json').read_text())
    assert before and all(digest(root/p)==sha for p,sha in before.items())
    staged=entries(Path('/stage'));assert staged
    finish.mkdir();(finish/'stage-before.json').write_text(json.dumps(staged,indent=2)+'\n')
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',XDG_CACHE_HOME='/build/cache')
    flags=subprocess.check_output(['pkg-config','--cflags','--libs','egl','glesv2'],
                                  env=dict(env,PKG_CONFIG_PATH='/stage/usr/lib/pkgconfig'),text=True).split()
    command=['cc','-Wall','-Wextra','-Werror','/src/toddy-probe.c','-I/stage/usr/include',
             '-L/stage/usr/lib','-Wl,-rpath-link,/stage/usr/lib',*flags,'-o','/build/mesa-consumer']
    with (finish/'consumer-compile.log').open('xb') as out:
        result=subprocess.run(command,env=env,stdout=out,stderr=subprocess.STDOUT)
    (finish/'consumer-compile.exit').write_text(str(result.returncode)+'\n')
    assert result.returncode==0,'Corrected staged consumer link failed'
    dynamic=subprocess.check_output(['readelf','-d','/build/mesa-consumer'],text=True)
    assert '(RPATH)' not in dynamic and '(RUNPATH)' not in dynamic
    with (root/'native-render.log').open('xb') as out:
        result=subprocess.run(['/build/mesa-consumer'],env=dict(env,LD_LIBRARY_PATH='/stage/usr/lib',
            LIBGL_DRIVERS_PATH='/stage/usr/lib/dri',LIBGL_ALWAYS_SOFTWARE='1',GALLIUM_DRIVER='llvmpipe',
            EGL_PLATFORM='surfaceless'),stdout=out,stderr=subprocess.STDOUT)
    (finish/'render.exit').write_text(str(result.returncode)+'\n')
    assert result.returncode==0,'Native staged renderer failed'
    text=(root/'native-render.log').read_text();assert 'renderer: llvmpipe' in text
    pixel=[int(v) for line in text.splitlines() if line.startswith('pixel: ') for v in line.removeprefix('pixel: ').split()]
    assert len(pixel)==4 and pixel[0]==0 and abs(pixel[1]-32)<=1 and abs(pixel[2]-64)<=1 and pixel[3]==255
    assert entries(Path('/stage'))==staged and all(digest(root/p)==sha for p,sha in before.items())
    merged={r['name']:{k:r[k] for k in ['name','result','returncode']} for r in original}
    for r in corrected:merged[r['name']]={k:r[k] for k in ['name','result','returncode']}
    assert all(r['result']=='OK' and r['returncode']==0 for r in merged.values())
    fs=os.statvfs('/build');assert fs.f_bavail*fs.f_frsize>=16*1024**3
    proof={'scope':'Reference software/virtual Wayland EGL/GBM profile, native CPU shader/raster/pixel proof; not GNOME/window/hardware acceptance',
        'registered_tests':48,'tests':list(merged.values()),'original_wrapper_exit':1,'test_recovery_wrapper_exit':1,
        'original_tests':{'passed':43,'failed':5,'log_sha256':digest(build/'meson-logs/testlog.json')},
        'affected_recheck':{'passed':5,'failed':0,'log_sha256':digest(corrected_path)},
        'upstream_log_sha256':digest(build/'meson-logs/testlog.json'),'consumer_exit':0,
        'native_render_stdout':text,'native_render_sha256':digest(root/'native-render.log'),
        'unchanged_compiled_elfs':len(before),'stage_unchanged_by_consumer':True,'stages':staged,
        'consumer_command':command,'consumer_runtime_rpath':False,'free_bytes_after_build':fs.f_bavail*fs.f_frsize,
        'recovery':'Missing test tools built/rechecked five only, original43passes reused. Complete first stage reused; consumer-only link-search fix3, no persistent RPATH. Original job1/job2 failures preserved.'}
    (root/'test-results.json').write_text(json.dumps(proof,indent=2)+'\n')


if __name__=='__main__':main()
