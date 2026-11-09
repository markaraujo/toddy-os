"""Promote only the exact native-tested Glycin profile through owned packaging."""
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from glycin_mime_compat import add_dds_canonical_alias,add_dds_decoder_alias
from package_copyright import write_copyright
from verify_stage import inspect_stage

ROOT=Path('/opt/toddy-build');TARGET=Path('/mnt/lfs')


def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def hashes(root):
    return {str(p.relative_to(root)):digest(p) for p in root.rglob('*') if p.is_file() and not p.is_symlink()}


def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    logs=Path('/var/log/toddy/phase2');work=TARGET/'sources/phase2/work/glycin-1'
    source=TARGET/'sources/phase2/inputs/glycin-2.1.5'
    assert (source/'toddy-build.py').read_bytes()==(ROOT/'scripts/build/phase2/glycin_build.py').read_bytes()
    assert (source/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/glycin-probe.c').read_bytes()
    assert (source/'toddy-crates.json').read_bytes()==(ROOT/'config/phase2/glycin-crates.lock.json').read_bytes()
    contract=json.loads((source/'toddy-crates.json').read_text());parent=next(p for p in contract['parents'] if p['name']=='glycin')
    assert len(parent['packages'])==307 and digest(source/'project/Cargo.lock')==parent['cargo_lock_sha256']
    harness=digest(ROOT/'scripts/build/phase2/isolated.sh')
    for name in ['glycin-1','glycin-tests-1','glycin-dds-1']:
        assert (logs/(name+'.exit')).read_text().strip()=='0'
        assert json.loads((logs/(name+'.job.json')).read_text())['harness_sha256']==harness
    command=json.loads((logs/'glycin-dds-1.job.json').read_text())['command']
    assert command[-4:]==['python3','-c',(ROOT/'scripts/build/phase2/glycin_dds_build.py').read_text(),
                         (ROOT/'scripts/build/phase2/glycin_mime_compat.py').read_text()]
    proof=json.loads((logs/'glycin-native-qualification.json').read_text());assert proof['all_selected_qualified']
    reports={}
    for n,row in proof['reports'].items():
        assert row['file']=='glycin-native-runtime-'+n+'.json' and n in ['1','4','5']
        r=json.loads((logs/row['file']).read_text())
        assert hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()==row['sha256']
        assert r['kernel']==proof['kernel']=='7.1.8-toddy' and r['pid1']=='systemd';reports[n]=r
    assert set(reports)=={'1','4','5'}
    tests=json.loads((work/'test-prepare-results.json').read_text())
    assert tests['executables']==reports['1']['test_artifacts']==reports['4']['test_artifacts']==reports['5']['test_artifacts']
    for row in tests['executables']:
        assert digest(work/Path(row['path']).relative_to('/build'))==row['sha256']
    baseline={r['name']:r for r in reports['1']['runs']};candidate={r['name']:r for r in reports['4']['runs']}
    final={r['name']:r for r in reports['5']['runs']}
    assert baseline['tests']['exit']==101 and '10 passed; 1 failed;' in baseline['tests']['stdout']
    for name,count in [('encoding',8),('editing',4),('change_memory_format',1)]:
        assert baseline[name]['exit']==0 and f'{count} passed; 0 failed;' in baseline[name]['stdout']
    assert candidate['native-GI-bwrap-images']['exit']==0
    assert final['tests']['exit']==0 and '1 passed; 0 failed;' in final['tests']['stdout']
    assert all(r['exit']==0 for r in reports['5']['runs'])
    reuse=reports['5']['reused_native_proof']
    assert reuse['report_sha256']==proof['reports']['1']['sha256']
    assert reuse['candidate_report_sha256']==proof['reports']['4']['sha256']
    assert reuse['candidate_gi_reused']=={'name':'native-GI-bwrap-images','exit':0}
    assert reports['5']['stage_file_hashes']==reports['4']['stage_file_hashes']==reuse['candidate_stage_file_hashes']
    for number,label in [('1','baseline'),('2','candidate')]:
        receipt=logs/('glycin-native-fixture.json' if number=='1' else 'glycin-native-fixture-dds.json')
        data=json.loads(receipt.read_text());assert data['state']=='complete'
        assert hashlib.sha256(json.dumps(data['payload'],sort_keys=True).encode()).hexdigest()==proof[label+'_fixture_payload_sha256']
    old_stage=TARGET/'sources/phase2/native-fixtures/glycin-1/stage'
    changed=json.loads((work/'dds-compat/results.json').read_text())
    assert changed==reports['5']['source_compatibility']==reports['4']['source_compatibility']
    assert changed['native_compile_exit']==0 and changed['source_changed_files']==['glycin-loaders/glycin-image-rs/src/main.rs']
    assert hashes(old_stage)==changed['stage_before']
    assert hashes(work/'stage')==changed['stage_after']==reports['5']['stage_file_hashes']
    assert sorted(k for k in changed['stage_before'] if changed['stage_before'][k]!=changed['stage_after'][k])==sorted(changed['changed_stage_files'])
    assert set(changed['changed_stage_files'])=={'usr/libexec/glycin-loaders/2+/glycin-image-rs','usr/share/glycin-loaders/2+/conf.d/glycin-image-rs.conf'}
    original=(source/'project/glycin-loaders/glycin-image-rs/src/main.rs').read_bytes()
    patched=(work/'dds-compat/project/glycin-loaders/glycin-image-rs/src/main.rs').read_bytes()
    assert patched==add_dds_decoder_alias(original)
    source_before=hashes(source/'project');source_after=hashes(work/'dds-compat/project')
    assert set(source_before)==set(source_after)
    assert [k for k in source_before if source_before[k]!=source_after[k]]==changed['source_changed_files']
    relative='usr/share/glycin-loaders/2+/conf.d/glycin-image-rs.conf'
    assert (work/'stage'/relative).read_bytes()==add_dds_canonical_alias((old_stage/relative).read_bytes())
    stage=work/'stage';verified=inspect_stage(stage);old_verified=inspect_stage(old_stage)
    assert set(verified['entries'])==set(old_verified['entries'])
    assert set(k for k in verified['entries'] if verified['entries'][k]!=old_verified['entries'][k])==set(changed['changed_stage_files'])
    destination=TARGET/'sources/stage/phase2-glycin'
    assert not destination.exists(),'Reconcile prior native transaction; never replay'
    assert not Path('/var/cache/toddy/packages/glycin_2.1.5-1+toddy1_amd64.deb').exists()
    shutil.copytree(stage,destination,symlinks=True);assert inspect_stage(destination)==verified
    archives=['glycin-2.1.5.tar.xz','glycin-2.1.5-vendor.tar.gz','rustc-1.97.1-src.tar.xz']
    write_copyright(destination,'glycin',archives)
    doc=destination/'usr/share/doc/glycin'
    (doc/'canonical-dds.patch').write_text(''.join(difflib.unified_diff(original.decode().splitlines(True),patched.decode().splitlines(True),
        fromfile='a/glycin-loaders/glycin-image-rs/src/main.rs',tofile='b/glycin-loaders/glycin-image-rs/src/main.rs')))
    shutil.copy2(ROOT/'scripts/build/phase2/glycin_mime_compat.py',doc/'toddy-mime-compat.py')
    (doc/'README.Toddy').write_text('Glycin bundle2.1.5/libglycin API2.1.0; selected image-rs and SVG loaders.\n'
        'ADR0143 adds canonical DDS spelling to existing decoder and configuration; exact patch/helper retained.\n'
        'HEIF/AVIF/JXL/raw, thumbnailer, GTK4 companion and Vala products omitted.\n'
        'Native selected24Rust cases and forced-bwrap GI pixels/refusal passed; ignored/filtered/unsupported cases are not passes.\n'
        'Original linked-directory external-SVG failure retained; native qualification uses byte-identical real-directory fixtures.\n'
        'Installed default-path native sandbox check remains part of the subsequent desktop boot gate.\n')
    depends='glibc (>= 2.44-1), gcc (>= 16.2.0-1), glib (>= 2.88.3-1+toddy1), lcms2 (= 2.19.1-1+toddy1), librsvg (= 2.62.3-1+toddy1), libseccomp (= 2.6.1-1+toddy1), bubblewrap (= 0.11.2-1+toddy1), shared-mime-info (= 2.5.1-1+toddy1)'
    subprocess.run([sys.executable,str(ROOT/'scripts/build/stage_package.py'),'glycin','2.1.5-1+toddy1',str(destination),
                    *[arg for name in archives for arg in ['--source',name]],'--recipe','scripts/build/phase2/glycin-install.sh',
                    '--depends',depends,'--install'],cwd=ROOT,check=True)
    (logs/'glycin-promoted-native-proof.json').write_text(json.dumps(proof,indent=2)+'\n')


if __name__=='__main__':main()
