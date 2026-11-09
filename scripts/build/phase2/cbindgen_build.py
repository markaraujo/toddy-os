"""Native offline C/C++ build-tool profile; omit unrelated Cython/unstable matrices."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    assert os.getuid()==101 and not list(Path('/stage').iterdir())
    assert not Path('/build/source').exists() and not Path('/build/test-results.json').exists()
    assert subprocess.check_output(['rustc','--version'],text=True).startswith('rustc 1.97.1 ')
    assert subprocess.check_output(['cargo','--version'],text=True).startswith('cargo 1.97.1 ')
    original=Path('/src/project');source=Path('/build/source');shutil.copytree(original,source,symlinks=True)
    home=Path('/build/cargo-home');home.mkdir();(home/'config.toml').write_bytes(Path('/src/toddy-cargo.toml').read_bytes())
    env=dict(os.environ,CARGO_HOME=str(home),CARGO_NET_OFFLINE='true',CARGO_BUILD_JOBS='4',CARGO_INCREMENTAL='0',CARGO_PROFILE_RELEASE_DEBUG='0',CARGO_PROFILE_TEST_DEBUG='0',CBINDGEN_TEST_VERIFY='1')
    commands=[('build',['cargo','build','--release','--frozen','--jobs','4','--target-dir','/build/compile']),('upstream-selected',['cargo','test','--release','--frozen','--jobs','4','--target-dir','/build/compile','--lib','--test','depfile'])]
    results=[]
    for name,command in commands:
        with Path('/build/'+name+'.log').open('xb') as output:r=subprocess.run(command,cwd=source,env=env,stdout=output,stderr=subprocess.STDOUT)
        Path('/build/'+name+'.exit').write_text(str(r.returncode)+'\n')
        assert r.returncode==0,name+' failed; retain source/cache/log'
        results.append({'name':name,'exit':r.returncode,'command':command,'log_sha256':digest(Path('/build/'+name+'.log'))})
    text=Path('/build/upstream-selected.log').read_text();summaries=re.findall(r'test result: (\w+)[.] (\d+) passed; (\d+) failed; (\d+) ignored;',text)
    assert summaries and all(s[0]=='ok' and int(s[2])==0 for s in summaries) and sum(int(s[1]) for s in summaries)>0
    binary=Path('/build/compile/release/cbindgen');before=digest(binary)
    with Path('/build/consumer.log').open('xb') as output:r=subprocess.run(['python3','/src/toddy-probe.py',str(binary),'/build/abi-consumer'],env=env,stdout=output,stderr=subprocess.STDOUT)
    Path('/build/consumer.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
    assert digest(binary)==before
    for p in original.rglob('*'):
        q=source/p.relative_to(original)
        if p.is_file() and not p.is_symlink() and p.name!='Cargo.lock':assert digest(q)==digest(p),'Tracked source/expectation changed'
    assert digest(source/'Cargo.lock')==digest(original/'Cargo.lock')
    stage=Path('/stage/usr/bin');stage.mkdir(parents=True);shutil.copy2(binary,stage/'cbindgen')
    proof={'scope':'Native offline cbindgen C/C++ build-tool profile only; no macro expansion/Cython/desktop qualification','version':'0.29.4','commands':results,'upstream_summaries':summaries,'upstream_selected_exit':0,'consumer_exit':0,'consumer':json.loads(Path('/build/abi-consumer/result.json').read_text()),'binary_sha256':before,'original_inputs_unchanged':True,'unqualified':['Full generated C/C++/Cython matrix not selected for basic C/C++ tool profile.','Book documents3profile tests relying on disabled Rust unstable features; not run/not passes.']}
    Path('/build/test-results.json').write_text(json.dumps(proof,indent=2)+'\n')

if __name__=='__main__':main()
