#!/bin/bash
# Frozen BLFS13.1 LibSass3.6.6; private copy for upstream autoreconf/build.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/configure.ac && -d /stage ]]
python3 - <<'PY'
import hashlib,json,os,signal,shutil,subprocess,time
from pathlib import Path
work=Path('/build');assert not (work/'compile').exists()
free=lambda:os.statvfs(work).f_bavail*os.statvfs(work).f_frsize
assert free()>=16*1024**3+256*1024**2
shutil.copytree('/src',work/'compile',symlinks=True)
env=dict(os.environ,LIBSASS_VERSION='3.6.6',CXXFLAGS='-O2 -g0',CFLAGS='-O2 -g0')
rows=[]
def run(name,args,cwd=work/'compile',extra=None):
    began=time.monotonic();stopped=False
    with (work/(name+'.log')).open('xb') as log:
        p=subprocess.Popen(args,cwd=cwd,env=dict(env,**(extra or {})),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        while p.poll() is None:
            if free()<16*1024**3:
                stopped=True;os.killpg(p.pid,signal.SIGTERM)
                try:p.wait(timeout=5)
                except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
                break
            time.sleep(2)
        code=p.wait()
    (work/(name+'.exit')).write_text(str(code)+'\n')
    row={'phase':name,'native_exit':code,'reserve_stop':stopped,'seconds':round(time.monotonic()-began,3),'free_bytes_after':free()};rows.append(row)
    (work/'phases.json').write_text(json.dumps(rows,indent=2)+'\n')
    assert code==0 and not stopped,row
run('bootstrap',['autoreconf','-fi'])
run('configure',['./configure','--prefix=/usr','--libdir=/usr/lib','--disable-static'])
run('build',['make','-j4'])
# Bundled independent C++ programs; the external Ruby Sass-spec matrix is not bundled.
run('upstream-cpp',['make','-j2','test'],cwd=work/'compile/test')
run('stage',['make','DESTDIR=/stage','install'])
flags=subprocess.check_output(['pkg-config','--cflags','--libs','libsass'],env=dict(env,PKG_CONFIG_PATH='/stage/usr/lib/pkgconfig'),text=True).split()
run('consumer-build',['cc','-D_GNU_SOURCE','/src/toddy-probe.c','-I/stage/usr/include','-o','/build/native-scss','-L/stage/usr/lib','-Wl,-rpath,/stage/usr/lib',*flags],cwd=work)
run('consumer',['/build/native-scss'],cwd=work)
unchanged=0
generated=None
for p in Path('/src').rglob('*'):
    if p.is_file() and not p.is_symlink() and p.suffix in ['.c','.cpp','.h','.hpp']:
        q=work/'compile'/p.relative_to('/src')
        if p.relative_to('/src').as_posix()=='include/sass/version.h':
            assert q.read_bytes()==p.read_bytes().replace(b'"[NA]"',b'"3.6.6"',1)
            generated={'file':'include/sass/version.h','input_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'change':'Only upstream configure version placeholder [NA] -> authenticated3.6.6'}
        else:assert q.read_bytes()==p.read_bytes();unchanged+=1
result={'scope':'Native stylesheet build dependency; not a desktop/catalog app',
    'phases':rows,'bundled_upstream_cpp_programs':2,'bundled_upstream_exit':0,'staged_consumer_exit':0,
    'unchanged_original_code_files':unchanged,'generated_version_header':generated,'version_source':'LIBSASS_VERSION=3.6.6, supported upstream version.sh override for authenticated tag archive without Git metadata',
    'limitations':'No bundled Ruby Sass-spec matrix; not claimed as passed. Used C API/nested navy SCSS/refusal and bundled C++ programs qualified; actual Libadwaita stylesheet build still required.'}
(work/'test-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
PY
