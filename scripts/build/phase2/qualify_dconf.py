"""Require original native runtime/ABI programs and actual CLI/GSettings persistence."""
import hashlib,json,tarfile
from pathlib import Path

def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
    source=Path('/mnt/lfs/sources/phase2/inputs/dconf-0.49.0-gvdb-1');work=Path('/mnt/lfs/sources/phase2/work/dconf-vendored-1');log=Path('/var/log/toddy/phase2')
    for a,b in [('toddy-build.sh','dconf-build.sh'),('toddy-probe.py','dconf-probe.py')]:assert (source/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
    assert (log/'dconf-gvdb-2.exit').read_text().strip()=='0'
    job=json.loads((log/'dconf-gvdb-2.job.json').read_text());assert job['command'][2:]==[str(source),str(work),'dbus-run-session','--','bash','/src/toddy-build.sh']
    prepared=json.loads((source/'toddy-prepared.json').read_text());extra=prepared['extra_source'];assert extra['name']=='dconf-gvdb' and extra['commit']=='4758f6fb7f889e074e13df3f914328f3eecb1fd3'
    archive=Path('/mnt/lfs/sources')/extra['filename'];assert digest(archive)==extra['sha256']
    expected={}
    with tarfile.open(archive) as t:
        for m in t:
            rel=Path(m.name).relative_to('gvdb-'+extra['commit']);assert '..' not in rel.parts
            if m.isfile():expected[str(rel)]=hashlib.sha256(t.extractfile(m).read()).hexdigest()
            else:assert m.isdir()
    actual={str(p.relative_to(source/'subprojects/gvdb')):digest(p) for p in (source/'subprojects/gvdb').rglob('*') if p.is_file()}
    assert actual==expected and len(actual)==15
    result=json.loads((work/'stage-results.json').read_text());assert result['compile_exit']==result['stage_exit']==0
    rows=[json.loads(s) for s in (work/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
    names={'gvdb - gvdb:gvdb','gvdb - gvdb:autoptr'}|{'dconf:'+n for n in ['paths','changeset','shm','gvdb','gdbus-thread','gdbus-filter','gdbus-thread-leak','gdbus-filter-leak','engine','client','writer','gsettings','libdconf','dconf']}
    assert len(rows)==16 and {r['name'] for r in rows}==names and all(r['result']=='OK' and r['returncode']==0 for r in rows)
    assert result['original_tests']==[{k:r[k] for k in ['name','result','returncode']} for r in rows]
    consumer=result['consumer'];assert consumer['isolated_user_database'] and not consumer['unrelated_configuration_changed']
    assert all(consumer['cycles'][0][k] for k in ['typed_write','malformed_refused','state_preserved'])
    assert all(consumer['cycles'][1][k] for k in ['persisted_after_bus_restart','dump','reset'])
    probe=(root/'scripts/build/phase2/dconf-gsettings-probe.py').read_text();job=json.loads((log/'dconf-gsettings-4.job.json').read_text())
    assert job['command'][2:]==[str(source),str(work),'python3','-c',probe,'/stage','/build/gsettings-1','stage']
    assert (log/'dconf-gsettings-4.exit').read_text().strip()=='0'
    settings=json.loads((log/'dconf-gsettings-4.log').read_text());assert settings['mode']=='stage' and not settings['unrelated_configuration_changed']
    assert len(settings['cycles'])==2 and all(r['backend']=='DConfSettingsBackend' for r in settings['cycles'])
    assert settings['cycles'][0]['write'] and settings['cycles'][0]['sync'] and settings['cycles'][1]['persisted_after_new_bus'] and settings['cycles'][1]['reset']
    for name,sha in result['stage_sha256'].items():assert digest(work/'stage'/name)==sha
