"""Qualify preserved results with only the upstream generated version header."""
import hashlib
import json
import os
from pathlib import Path


def main():
    assert os.getuid()==101
    work=Path('/build');out=work/'qualify-2';out.mkdir()
    phases=json.loads((work/'phases.json').read_text())
    assert [r['phase'] for r in phases]==['bootstrap','configure','build','upstream-cpp','stage','consumer-build','consumer']
    assert all(r['native_exit']==0 and not r['reserve_stop'] for r in phases)
    for r in phases:assert (work/(r['phase']+'.exit')).read_text().strip()=='0'
    log=(work/'upstream-cpp.log').read_text()
    assert 'test_shared_ptr: Passed: 11, failed: 0.' in log and 'test_util_string: Passed: 16, failed: 0.' in log
    unchanged=0;generated=None;binaries={};stage={}
    for p in Path('/src').rglob('*'):
        if p.is_file() and not p.is_symlink() and p.suffix in ['.c','.cpp','.h','.hpp']:
            q=work/'compile'/p.relative_to('/src')
            if p.relative_to('/src').as_posix()=='include/sass/version.h':
                assert q.read_bytes()==p.read_bytes().replace(b'"[NA]"',b'"3.6.6"',1)
                generated={'file':'include/sass/version.h','input_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'change':'Only upstream configure version placeholder [NA] -> authenticated3.6.6'}
            else:assert q.read_bytes()==p.read_bytes();unchanged+=1
    assert generated and unchanged
    for p in (work/'compile').rglob('*'):
        if p.is_file() and not p.is_symlink():
            with p.open('rb') as f:
                if f.read(4)==b'\x7fELF':
                    f.seek(0);binaries[str(p.relative_to(work/'compile'))]=hashlib.file_digest(f,'sha256').hexdigest()
    for p in Path('/stage').rglob('*'):
        if p.is_symlink():stage[str(p.relative_to('/stage'))]={'link':str(p.readlink())}
        elif p.is_file():
            with p.open('rb') as f:stage[str(p.relative_to('/stage'))]={'sha256':hashlib.file_digest(f,'sha256').hexdigest()}
    assert binaries and stage
    (out/'binaries.json').write_text(json.dumps(binaries,indent=2)+'\n')
    (out/'stage-files.json').write_text(json.dumps(stage,indent=2)+'\n')
    result={'scope':'Native stylesheet dependency; exact generated version metadata qualification only',
        'phases':phases,'bundled_upstream_cpp_programs':2,'bundled_upstream_cpp_cases':27,'bundled_upstream_exit':0,'staged_consumer_exit':0,
        'unchanged_original_code_files':unchanged,'generated_version_header':generated,'preserved_compiled_elf_files':len(binaries),'preserved_stage_files_links':len(stage),
        'limitations':'External Ruby Sass-spec matrix not bundled or claimed passed. Native CSS API/negative input/two bundled C++ programs qualified; actual Libadwaita stylesheet compilation remains required.'}
    (work/'test-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
