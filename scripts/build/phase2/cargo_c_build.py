"""Build/test cargo-c only in the native isolated target, using frozen sources."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    assert os.getuid()==101 and not list(Path('/stage').iterdir()) and not Path('/build/test-results.json').exists()
    fs=os.statvfs('/build');assert fs.f_bavail*fs.f_frsize>=20*1024**3
    assert subprocess.check_output(['rustc','--version'],text=True).startswith('rustc 1.97.1 ')
    assert subprocess.check_output(['cargo','--version'],text=True).startswith('cargo 1.97.1 ')
    home=Path('/build/cargo-home')
    if sys.argv[1:]==['--resume-readability']:
        assert Path('/build/build.exit').read_text().strip()=='101'
        text=Path('/build/build.log').read_text()
        assert 'fnv-1.0.7/Cargo.toml.orig' in text and 'Permission denied (os error 13)' in text
        assert 'Compiling ' not in text
        assert (home/'config.toml').read_bytes()==Path('/src/toddy-cargo.toml').read_bytes()
        expected={str(p.relative_to('/src/project')) for p in Path('/src/project').rglob('*') if p.is_file() or p.is_symlink()}
        actual={str(p.relative_to('/build/source')) for p in Path('/build/source').rglob('*') if p.is_file() or p.is_symlink()}
        assert actual==expected,'Unexpected private source change; inspect before resuming'
        for original in Path('/src/project').rglob('*'):
            copy=Path('/build/source')/original.relative_to('/src/project')
            if original.is_symlink():assert copy.is_symlink() and os.readlink(original)==os.readlink(copy)
            elif original.is_file():assert copy.is_file() and not copy.is_symlink() and digest(copy)==digest(original)
        for suffix in ['log','exit']:
            destination=Path('/build/build-readability-failed-1.'+suffix);assert not destination.exists()
            Path('/build/build.'+suffix).rename(destination)
    else:
        assert not sys.argv[1:] and not Path('/build/source').exists()
        shutil.copytree('/src/project','/build/source',symlinks=True)
        home.mkdir();(home/'config.toml').write_bytes(Path('/src/toddy-cargo.toml').read_bytes())
    env=dict(os.environ,CARGO_HOME=str(home),CARGO_NET_OFFLINE='true',CARGO_BUILD_JOBS='4',
             CARGO_PROFILE_RELEASE_DEBUG='0',CARGO_PROFILE_TEST_DEBUG='0',OPENSSL_NO_VENDOR='1')
    commands=[('build',['cargo','build','--release','--frozen','--jobs','4','--target-dir','/build/compile']),
              ('upstream-tests',['cargo','test','--release','--frozen','--jobs','4','--target-dir','/build/compile'])]
    results=[]
    for name,command in commands:
        with Path('/build/'+name+'.log').open('xb') as output:
            result=subprocess.run(command,cwd='/build/source',env=env,stdout=output,stderr=subprocess.STDOUT)
        Path('/build/'+name+'.exit').write_text(str(result.returncode)+'\n')
        assert result.returncode==0,name+' failed; preserve compiled work'
        results.append({'name':name,'native_exit':result.returncode,'command':command,'log_sha256':digest(Path('/build/'+name+'.log'))})
        print(json.dumps({'phase':name,'native_exit':result.returncode}),flush=True)
    text=Path('/build/upstream-tests.log').read_text()
    summaries=re.findall(r'test result: (\w+)[.] (\d+) passed; (\d+) failed; (\d+) ignored;',text)
    assert summaries and all(s[0]=='ok' and int(s[2])==0 for s in summaries)
    assert sum(int(s[1]) for s in summaries)>=6
    stage=Path('/stage/usr/bin');stage.mkdir(parents=True)
    for name in ['cargo-capi','cargo-cbuild','cargo-cinstall','cargo-ctest']:
        source=Path('/build/compile/release')/name;assert source.is_file() and not source.is_symlink()
        shutil.copy2(source,stage/name)
    env['PATH']=str(stage)+':'+env['PATH']
    with Path('/build/consumer.log').open('xb') as output:
        result=subprocess.run(['python3','/src/toddy-probe.py','/build/capi-consumer'],env=env,stdout=output,stderr=subprocess.STDOUT)
    Path('/build/consumer.exit').write_text(str(result.returncode)+'\n')
    assert result.returncode==0,'Native generated C ABI consumer failed'
    fs=os.statvfs('/build');assert fs.f_bavail*fs.f_frsize>=16*1024**3
    entries={p.name:{'sha256':digest(p),'size':p.stat().st_size} for p in stage.iterdir()}
    Path('/build/test-results.json').write_text(json.dumps({'scope':'Native offline cargo-c build-tool source/test/stage and actual C ABI consumers; not an image/runtime inclusion or UI acceptance',
        'version':'0.10.24+cargo-0.98.0','commands':results,'upstream_summaries':summaries,
        'consumer_exit':0,'consumer':json.loads(Path('/build/capi-consumer/results.json').read_text()),
        'stage_bins':entries,'free_bytes_after_build':fs.f_bavail*fs.f_frsize},indent=2)+'\n')


if __name__=='__main__':main()
