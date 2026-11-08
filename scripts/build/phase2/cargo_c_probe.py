"""Native cargo-c plugins generate/install a real Rust C ABI and C consumers."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys


def main():
    destination=Path(sys.argv[1]);destination.mkdir()
    env=dict(os.environ,CARGO_NET_OFFLINE='true',CARGO_BUILD_JOBS='4')
    checks=[]

    def run(name,command,cwd=destination,extra=None):
        with (destination/(name+'.log')).open('xb') as output:
            result=subprocess.run(command,cwd=cwd,env=dict(env,**(extra or {})),stdout=output,stderr=subprocess.STDOUT)
        (destination/(name+'.exit')).write_text(str(result.returncode)+'\n')
        checks.append({'name':name,'native_exit':result.returncode,'command':command})
        assert result.returncode==0,name+' failed'

    versions={}
    for plugin in ['capi','cbuild','cinstall','ctest']:
        run('version-'+plugin,['cargo-'+plugin,'--version'])
        text=(destination/('version-'+plugin+'.log')).read_text()
        assert '0.10.24+cargo-0.98.0' in text,text
        versions[plugin]=text.strip()
    source=destination/'source';(source/'src').mkdir(parents=True)
    (source/'Cargo.toml').write_text('''[package]
name="toddy-fixture"
version="0.1.0"
edition="2021"
[lib]
path="src/lib.rs"
[features]
capi=[]
[package.metadata.capi.header]
name="toddy_fixture"
subdirectory=""
[package.metadata.capi.library]
name="toddy_fixture"
[package.metadata.capi.pkg_config]
name="Toddy fixture"
filename="toddy-fixture"
''')
    (source/'cbindgen.toml').write_text('language="C"\ninclude_guard="TODDY_FIXTURE_H"\n')
    (source/'src/lib.rs').write_text('''#[no_mangle]
pub extern "C" fn toddy_fixture_answer()->i32 { 42 }
#[cfg(test)] mod tests { #[test] fn answer(){ assert_eq!(super::toddy_fixture_answer(),42); } }
''')
    run('cbuild',['cargo','cbuild','--release','--offline'],source)
    stage=destination/'stage'
    run('cinstall',['cargo','cinstall','--release','--offline','--prefix=/usr','--libdir=lib',
                     '--destdir='+str(stage)],source)
    run('ctest',['cargo','ctest','--release','--offline'],source)
    assert (stage/'usr/include/toddy_fixture.h').is_file()
    assert (stage/'usr/lib/libtoddy_fixture.a').is_file()
    assert list((stage/'usr/lib').glob('libtoddy_fixture.so*'))
    pc=stage/'usr/lib/pkgconfig/toddy-fixture.pc';assert pc.is_file() and 'prefix=/usr' in pc.read_text()
    pc_env=dict(env,PKG_CONFIG_PATH=str(pc.parent),PKG_CONFIG_SYSROOT_DIR=str(stage))
    assert subprocess.check_output(['pkg-config','--modversion','toddy-fixture'],env=pc_env,text=True).strip()=='0.1.0'
    flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','toddy-fixture'],env=pc_env,text=True))
    c=destination/'consumer.c';c.write_text('#include <toddy_fixture.h>\nint main(void){return toddy_fixture_answer()==42?0:1;}\n')
    run('c-shared-compile',['cc','-Wall','-Wextra','-Werror',str(c),*flags,'-o',str(destination/'shared-consumer')])
    run('c-shared-execute',[str(destination/'shared-consumer')],extra={'LD_LIBRARY_PATH':str(stage/'usr/lib')})
    static_flags=shlex.split(subprocess.check_output(['pkg-config','--libs','--static','toddy-fixture'],env=pc_env,text=True))
    static_flags=[f for f in static_flags if f!='-ltoddy_fixture' and not f.startswith('-L')]
    run('c-static-compile',['cc','-Wall','-Wextra','-Werror',str(c),'-I'+str(stage/'usr/include'),
                            str(stage/'usr/lib/libtoddy_fixture.a'),*static_flags,'-o',str(destination/'static-consumer')])
    run('c-static-execute',[str(destination/'static-consumer')])
    proof={'scope':'Native build-tool plugins, real generated header/pkg-config/shared+static C ABI and Rust fixture test; no product UI',
           'uid':os.getuid(),'versions':versions,'checks':checks,'expected_answer':42,'prefix':'/usr','fixture_acquisition':'offline, no external dependencies'}
    (destination/'results.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))


if __name__=='__main__':main()
