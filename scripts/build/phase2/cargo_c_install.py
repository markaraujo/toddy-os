"""Promote only qualified native cargo-c plugins; no compiler/source test replay."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

from package_copyright import write_copyright
from verify_stage import inspect_stage

ROOT=Path('/opt/toddy-build')


def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    logs=Path('/var/log/toddy/phase2');source=Path('/mnt/lfs/sources/phase2/inputs/cargo-c-tool-0.10.24')
    work=Path('/mnt/lfs/sources/phase2/work/cargo-c-1');assert work.resolve()==work
    config=json.loads((source/'toddy-crates.json').read_text())
    assert (source/'toddy-crates.json').read_bytes()==(ROOT/'config/phase2/rust-crates.lock.json').read_bytes()
    parent=next(p for p in config['parents'] if p['name']=='cargo-c')
    assert digest(source/'project/Cargo.lock')==parent['cargo_lock_sha256']
    prepared=json.loads((source/'toddy-prepared.json').read_text())
    assert prepared['registry_crates']==418 and prepared['cargo_lock_sha256']==parent['cargo_lock_sha256']
    names=['cargo-capi','cargo-cbuild','cargo-cinstall','cargo-ctest']
    original_job=json.loads((logs/'cargo-c-1.job.json').read_text())
    harness=digest(ROOT/'scripts/build/phase2/isolated.sh');assert original_job['harness_sha256']==harness
    legacy=(logs/'cargo-c-probe-recovery-3.job.json').exists()
    if legacy:
        assert (logs/'cargo-c-1.exit').read_text().strip()=='1'
        assert (logs/'cargo-c-readability-resume-2.exit').read_text().strip()=='1'
        assert (logs/'cargo-c-probe-recovery-3.exit').read_text().strip()=='0'
        assert digest(source/'toddy-build.py')=='af413407cfd4c09a6170bcf851d12df9b6f3b2c3e8c77f3ddbf190b0c0a16d5e'
        assert digest(source/'toddy-probe.py')=='c19d6d5b92993e3c684c73e83d88a62bc3c9a8adcd1cbbf8a82f27d828a44cf5'
        assert (work/'build-readability-failed-1.exit').read_text().strip()=='101'
        assert 'fnv-1.0.7/Cargo.toml.orig' in (work/'build-readability-failed-1.log').read_text()
        operation=json.loads((logs/'cargo-c-public-readability.json').read_text())
        assert operation['state']=='complete' and operation['prepared_sha256']==digest(source/'toddy-prepared.json')
        assert len(operation['planned_changes'])==6
        for change in operation['planned_changes']:
            path=source/'vendor'/change['path']
            assert path.resolve().is_relative_to(source/'vendor') and digest(path)==change['content_sha256']
            assert path.stat().st_mode & 0o777==change['after_mode']==0o644
        resume=json.loads((logs/'cargo-c-readability-resume-2.job.json').read_text())
        assert resume['harness_sha256']==harness
        assert resume['command'][-4:]==['python3','-c',(ROOT/'scripts/build/phase2/cargo_c_build.py').read_text(),'--resume-readability']
        final=json.loads((logs/'cargo-c-probe-recovery-3.job.json').read_text())
        assert final['harness_sha256']==harness
        assert final['command'][-3:]==['python3','-c',(ROOT/'scripts/build/phase2/cargo_c_probe_recovery.py').read_text()]
        assert (work/'consumer.exit').read_text().strip()=='1'
        assert (work/'probe-recovery-3/probe.exit').read_text().strip()=='0'
        proof=json.loads((work/'capi-tools-qualified.json').read_text())
        assert proof['consumer_exit']==0
        for name,sha in proof['stage_bins_unchanged'].items():assert digest(work/'stage/usr/bin'/name)==sha
        consumer=proof['consumer']
    else:
        assert (logs/'cargo-c-1.exit').read_text().strip()=='0'
        assert (source/'toddy-build.py').read_bytes()==(ROOT/'scripts/build/phase2/cargo_c_build.py').read_bytes()
        assert (source/'toddy-probe.py').read_bytes()==(ROOT/'scripts/build/phase2/cargo_c_probe.py').read_bytes()
        proof=json.loads((work/'test-results.json').read_text());assert proof['consumer_exit']==0
        consumer=proof['consumer']
    for label in ['build','upstream-tests']:assert (work/(label+'.exit')).read_text().strip()=='0'
    text=(work/'upstream-tests.log').read_text()
    summaries=re.findall(r'test result: (\w+)[.] (\d+) passed; (\d+) failed; (\d+) ignored;',text)
    assert summaries and all(s[0]=='ok' and int(s[2])==int(s[3])==0 for s in summaries)
    assert sum(int(s[1]) for s in summaries)==25
    assert consumer['uid']==101 and consumer['expected_answer']==42
    assert set(consumer['versions'])=={'capi','cbuild','cinstall','ctest'}
    expected={'version-capi','version-cbuild','version-cinstall','version-ctest','cbuild','cinstall','ctest',
              'c-shared-compile','c-shared-execute','c-static-compile','c-static-execute'}
    assert len(consumer['checks'])==len(expected) and {r['name'] for r in consumer['checks']}==expected
    assert all(r['native_exit']==0 for r in consumer['checks'])
    consumer_dir=work/('capi-consumer-recovery-3' if legacy else 'capi-consumer')
    for name in expected:assert (consumer_dir/(name+'.exit')).read_text().strip()=='0'
    assert 'test result: ok. 1 passed; 0 failed; 0 ignored;' in (consumer_dir/'ctest.log').read_text()
    stage=work/'stage';verified=inspect_stage(stage)
    actual={p.name for p in (stage/'usr/bin').iterdir()};assert actual==set(names)
    assert all(str(p.relative_to(stage)) in {'usr','usr/bin'} or str(p.relative_to(stage)) in {'usr/bin/'+n for n in names} for p in stage.rglob('*'))
    destination=Path('/mnt/lfs/sources/stage/phase2-cargo-c')
    assert not destination.exists() and not destination.is_symlink(),'Reconcile prior native transaction; no install replay'
    shutil.copytree(stage,destination,symlinks=True);assert inspect_stage(destination)==verified
    (logs/'cargo-c-stage.json').write_text(json.dumps(verified,indent=2)+'\n')
    archives=['cargo-c-0.10.24.tar.gz','cargo-c-0.10.24-vendor.tar.gz',
              'cargo-c-0.10.24+cargo-0.98.0.crate','rustc-1.97.1-src.tar.xz']
    write_copyright(destination,'cargo-c',archives)
    subprocess.run([sys.executable,str(ROOT/'scripts/build/stage_package.py'),'cargo-c','0.10.24-1+toddy1',str(destination),
                    *[arg for name in archives for arg in ['--source',name]],'--recipe','scripts/build/phase2/cargo-c-install.sh',
                    '--depends','rustc (= 1.97.1-1+toddy1), glibc (>= 2.44-1), gcc (>= 16.2.0-1), openssl (>= 4.0.3-1), curl (>= 8.23.0-1), sqlite (>= 3.53.4-1), zlib (>= 1.3.2-1)',
                    '--install'],cwd=ROOT,check=True)


if __name__=='__main__':main()
