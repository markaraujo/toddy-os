"""Qualify only original single-initialization module/bus profile; retain exact skip."""
import hashlib,json
from pathlib import Path

def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root,log):
    source=Path('/mnt/lfs/sources/phase2/inputs/dbus-python-1.4.0');work=Path('/mnt/lfs/sources/phase2/work/dbus-python-1')
    assert (source/'toddy-probe.py').read_bytes()==(root/'scripts/build/phase2/dbus-python-probe.py').read_bytes()
    legacy=(log/'dbus-python-verify-2.exit').exists()
    if legacy:
        assert (log/'dbus-python-1.exit').read_text().strip()=='1' and (log/'dbus-python-verify-2.exit').read_text().strip()=='0'
        assert digest(source/'toddy-build.sh')=='3d28303009ad42cf4cc0ccc3abacb78cbf5ae0a871c8d3be638c5a628ca18ed5'
        assert json.loads((log/'dbus-python-verify-2.job.json').read_text())['command'][-1]==(root/'scripts/build/phase2/dbus_python_finish.py').read_text()
    else:
        assert (log/'dbus-python-1.exit').read_text().strip()=='0'
        assert (source/'toddy-build.sh').read_bytes()==(root/'scripts/build/phase2/dbus-python-build.sh').read_bytes()
    r=json.loads((work/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==r['native_consumer_exit']==0
    assert r['upstream_passed_programs']==7 and r['upstream_skipped_programs']==1
    rows=[json.loads(s) for s in (work/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
    assert len(rows)==8
    for row in rows:
        if row['name']=='dbus-python:import-repeatedly':assert row['result']=='SKIP' and row['returncode']==0 and row['stdout']=='1..1\nok 1 # SKIP https://gitlab.freedesktop.org/dbus/dbus-python/-/issues/55\n' and not row.get('stderr')
        else:assert row['result']=='OK' and row['returncode']==0
    assert '#if DBUSPY_PY_VERSION_AT_LEAST(3, 12, 0, 0)' in (source/'test/import-repeatedly.c').read_text()
    for p,sha in r.get('unchanged_compiled_elfs',{}).items():assert digest(work/p)==sha
    for p,sha in r['stage_sha256'].items():assert digest(work/'stage'/p)==sha
    c=r['consumer'];assert c['version']=='1.4.0' and c['distinct_connections'] and len(c['cycles'])==2
    assert all(x['uid']==101 and x['typed_uid'] and x['missing_peer_refused'] and x['name_acquire_release'] and x['recovery_call'] for x in c['cycles'])
