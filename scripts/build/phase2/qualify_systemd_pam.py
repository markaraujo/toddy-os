"""Gate only the same-version PAM delta; boot/session acceptance stays separate."""
import hashlib,json,subprocess
from pathlib import Path
from systemd_pam_abi import compare
from verify_stage import inspect_stage
ROOT=Path('/opt/toddy-build');LOG=Path('/var/log/toddy/phase2');WORK=Path('/mnt/lfs/sources/phase2/work/systemd-pam-1')
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify():
    assert (LOG/'systemd-pam-1.exit').read_text().strip()=='1' and (LOG/'systemd-pam-stage-2.exit').read_text().strip()=='0'
    recipe=(ROOT/'scripts/build/phase2/systemd-pam-build.py').read_text()
    expected="import sys;sys.argv=['systemd-pam-build','--stage-only'];exec(compile("+repr(recipe)+",'systemd-pam-build','exec'))"
    assert json.loads((LOG/'systemd-pam-stage-2.job.json').read_text())['command'][-1]==expected
    result=json.loads((WORK/'stage-results.json').read_text());assert result['compile_exit']==result['stage_exit']==result['staged_version_exit']==result['staged_module_load_exit']==0
    assert result['feature_delta']=={'HAVE_PAM':{'old':'0','new':'1'}} and len(result['artifacts'])==6
    assert len(result['unchanged_selected_artifacts'])==12
    for p,sha in result['unchanged_selected_artifacts'].items():assert digest(WORK/'compile'/p)==sha
    for p,sha in result['artifacts'].items():assert digest(WORK/'stage'/p)==sha
    raw=(LOG/'native-systemd-pam-1-report.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='df35f12211481740cc9721553e666ff3bb7cf35221bc4a3685b7d99b1002dd13'
    native=json.loads(raw);assert native['kernel']=='7.1.8-toddy' and native['cgroup_filesystem']=='cgroup2'
    assert [r['name'] for r in native['runs']]==['test-load-fragment','test-unit-serialize'] and all(r['exit']==0 and not r['skip_diagnostics'] for r in native['runs'])
    fixture=Path('/mnt/lfs/sources/phase2/native-fixtures/systemd-pam-1');assert digest(fixture/'accepted.json')==native['fixture_manifest_sha256']
    accepted=json.loads((fixture/'accepted.json').read_text());assert len(accepted['artifacts'])==native['unchanged_fixture_files']==12
    for p,sha in accepted['artifacts'].items():assert digest(fixture/p)==sha
    assert inspect_stage(fixture/'stage')==inspect_stage(WORK/'stage')
    manifest=json.loads((LOG/'systemd-pam-source-manifest-1.json').read_text());assert hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()==native['source_manifest_sha256']
    assert len([r for r in manifest.values() if 'sha256' in r])==native['unchanged_source_files']==7193
    source=Path('/mnt/lfs/sources/phase2/inputs/systemd-pam-261.2')
    options=subprocess.check_output(['findmnt','-n','-o','OPTIONS','--mountpoint',str(source)],text=True).strip().split(',');assert {'ro','nosuid','nodev'}<=set(options)
    for p,row in manifest.items():
        if 'sha256' in row:assert not (source/p).is_symlink() and digest(source/p)==row['sha256']
        else:assert (source/p).is_symlink() and str((source/p).readlink())==row['symlink']
    abi=compare();assert abi['accepted_existing_export_surface']
    return result,abi
if __name__=='__main__':
    _,abi=qualify();print(json.dumps(abi,indent=2))
