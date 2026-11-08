"""Compile original tests offline without executing sandbox tests on the builder."""
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main():
    work=Path('/build'); source=Path('/src/project')
    assert os.getuid()==101
    result=json.loads((work/'stage-results.json').read_text())
    assert result['native_compile_exit']==0 and not result['package_promotable']
    before=hashlib.sha256((source/'Cargo.lock').read_bytes()).hexdigest()
    assert before==result['cargo_lock_sha256']
    env=dict(os.environ,PATH='/build/tools:/usr/bin:/usr/sbin',CARGO_HOME='/build/compile/cargo-home',
             CARGO_NET_OFFLINE='true',CARGO_BUILD_JOBS='2',RUSTFLAGS='-Cdebuginfo=0',CARGO_INCREMENTAL='0',
             GLYCIN_TEST_SKIP_EXT='avif,heic,heif,jxl',RUST_LOG='warn')
    # The frozen /build/tools/cargo wrapper inserts --locked and --offline.
    args=['cargo','test','--no-run','--message-format=json',
          '-p','tests','-p','glycin-image-rs','-p','glycin-svg',
          '--target-dir','/build/compile/cargo-target/tests','--profile','release',
          '--manifest-path','/src/project/Cargo.toml']
    with (work/'test-compile.jsonl').open('xb') as output, (work/'test-compile.log').open('xb') as log:
        done=subprocess.run(args,env=env,stdout=output,stderr=log)
    (work/'test-compile.exit').write_text(str(done.returncode)+'\n')
    assert done.returncode==0
    assert hashlib.sha256((source/'Cargo.lock').read_bytes()).hexdigest()==before
    artifacts=[]
    for line in (work/'test-compile.jsonl').read_text().splitlines():
        row=json.loads(line)
        if row.get('reason')=='compiler-artifact' and row.get('executable') and row['profile']['test']:
            path=Path(row['executable']);assert path.is_relative_to('/build/compile/cargo-target/tests')
            artifacts.append({'name':row['target']['name'],'path':str(path),
                              'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size})
    assert {r['name'] for r in artifacts}=={'change_memory_format','editing','encoding','tests',
                                         'dbus_api_stability','glycin-image-rs','glycin-svg'}
    receipt={'scope':'Original native test executables compiled only; runtime remains pending',
             'cargo_lock_sha256':before,'test_compile_exit':0,'executables':artifacts,
             'unsupported_extensions':['avif','heic','heif','jxl'],
             'runtime_exclusions':{'encoding':['write_avif'],
                                   'dbus_api_stability':'Original upstream ignored test, not a pass'},
             'package_promotable':False}
    (work/'test-prepare-results.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))


if __name__=='__main__':main()
