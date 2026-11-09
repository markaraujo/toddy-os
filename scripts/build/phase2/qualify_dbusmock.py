"""Qualify the bounded core test-tool profile without claiming external services."""
import hashlib,json
from pathlib import Path

def qualify(root):
    source=Path('/mnt/lfs/sources/phase2/inputs/python_dbusmock-0.38.1')
    work=Path('/mnt/lfs/sources/phase2/work/python-dbusmock-1')
    for a,b in [('toddy-build.sh','python-dbusmock-build.sh'),('toddy-probe.py','python-dbusmock-probe.py')]:
        assert (source/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
    log=Path('/var/log/toddy/phase2')
    assert (log/'python-dbusmock-2.exit').read_text().strip()=='0'
    job=json.loads((log/'python-dbusmock-2.job.json').read_text())
    assert job['command'][2:4]==[str(source),str(work)]
    result=json.loads((work/'stage-results.json').read_text())
    assert result['compile_exit']==result['stage_exit']==0
    assert result['original_cases']==61 and result['passed']==60
    assert result['skipped']==[{'name':'test_template_upower_exec','reason':{'type':'pytest.skip','message':'No upower installed'}}]
    assert result['consumer']['version']=='0.38.1'
    cycles=result['consumer']['cycles'];assert len(cycles)==2 and cycles[0]['owner']!=cycles[1]['owner']
    assert all(r['typed_echo']==42 and r['unknown_method_refused'] and r['recovery'] for r in cycles)
    for name,sha in result['stage_sha256'].items():
        assert hashlib.sha256((work/'stage'/name).read_bytes()).hexdigest()==sha
