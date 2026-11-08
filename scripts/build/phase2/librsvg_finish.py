"""Stage the preserved renderer with a narrowly proven Pango golden exception."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess


def main():
    assert os.getuid()==101 and not list(Path('/stage').iterdir())
    assert Path('/build/build.exit').read_text().strip()=='0'
    assert Path('/build/upstream-tests.exit').read_text().strip()=='1'
    rows=[json.loads(line) for line in Path('/build/compile/meson-logs/testlog.json').read_text().splitlines()]
    assert len(rows)==5
    failures=[r for r in rows if r['result']!='OK']
    assert len(failures)==1 and failures[0]['name']=='librsvg:Rust tests (rsvg)' and failures[0]['returncode']==1
    assert all(r['returncode']==0 for r in rows if r['result']=='OK')
    text=failures[0]['stdout']
    assert text.count(' ... FAILED')==1 and 'test tests::svg1_1_text_text_03_b_svg ... FAILED' in text
    assert 'FAILED. 753 passed; 1 failed; 0 ignored;' in text
    oracle=json.loads(Path('/build/strike-oracle-5/metrics.json').read_text())
    assert Path('/build/strike-oracle-5/oracle.exit').read_text().strip()=='0'
    assert oracle['pango_version']=='1.58.2' and oracle['changed_pixels']==12 and oracle['outside_decoration_changes']==0
    assert oracle['logical_width']==177.484375 and oracle['ink_x']==2.640625 and oracle['ink_width']==172.71875
    assert oracle['upstream_golden_passed'] is False
    manifest=json.loads(Path('/build/reference-diagnose-3/binaries-before.json').read_text())
    def verify_binaries():
        for relative,expected in manifest.items():
            with (Path('/build/compile')/relative).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==expected
    verify_binaries()
    output=Path('/build/finish-6');output.mkdir()
    checks=[]
    def run(name,command,extra=None):
        with (output/(name+'.log')).open('xb') as log:
            r=subprocess.run(command,env=dict(os.environ,**(extra or {})),stdout=log,stderr=subprocess.STDOUT)
        (output/(name+'.exit')).write_text(str(r.returncode)+'\n')
        checks.append({'name':name,'native_exit':r.returncode,'command':command});assert r.returncode==0,name
    run('stage',['ninja','-C','/build/compile','install'],{'DESTDIR':'/stage','CARGO_HOME':'/build/cargo-home','CARGO_NET_OFFLINE':'true','CARGO_BUILD_JOBS':'4','CARGO_PROFILE_RELEASE_DEBUG':'0','CARGO_PROFILE_TEST_DEBUG':'0','CARGO_INCREMENTAL':'0'})
    modules=list(Path('/stage/usr/lib/gdk-pixbuf-2.0/2.10.0/loaders').glob('*.so'))
    assert len(modules)==1 and modules[0].name=='libpixbufloader_svg.so'
    run('loader-query',['gdk-pixbuf-query-loaders',str(modules[0])],{'LD_LIBRARY_PATH':'/stage/usr/lib'})
    cache=output/'loader-query.log';text=cache.read_text();assert '"svg"' in text and str(modules[0]) in text
    flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','librsvg-2.0','gdk-pixbuf-2.0'],env=dict(os.environ,PKG_CONFIG_PATH='/stage/usr/lib/pkgconfig'),text=True))
    run('consumer-compile',['cc','-Wall','-Wextra','-Werror','/src/toddy-probe.c','-I/stage/usr/include/librsvg-2.0','-L/stage/usr/lib',*flags,'-o',str(output/'svg-consumer')])
    run('consumer',[str(output/'svg-consumer')],{'LD_LIBRARY_PATH':'/stage/usr/lib','GDK_PIXBUF_MODULE_FILE':str(cache)})
    verify_binaries()
    fs=os.statvfs('/build');free=fs.f_bavail*fs.f_frsize;assert free>=16*1024**3
    proof={'scope':'Native SVG renderer/staged C API and Gdk loader; upstream golden still failed, selected Pango1.58 geometry independently qualified under ADR0134; no GUI/session acceptance',
        'tests':[{'name':r['name'],'result':r['result'],'returncode':r['returncode']} for r in rows],
        'known_golden_failure':{'name':'tests::svg1_1_text_text_03_b_svg','upstream_passed':False,'pango_geometry_oracle':oracle},
        'checks':checks,'staged_consumer_exit':0,'consumer_stdout':(output/'consumer.log').read_text(),
        'unchanged_compiled_elf_files':len(manifest),'free_bytes_after_stage':free,
        'generated_cache_scope':'Private staged-module cache only; actual installed cache requires owned controlled update'}
    Path('/build/test-results.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))


if __name__=='__main__':main()
