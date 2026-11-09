"""Require unchanged full source/stage and actual native authorization before privilege."""
import hashlib,json
from pathlib import Path
from accept_polkit_native import validate

def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
    source=Path('/mnt/lfs/sources/phase2/inputs/polkit-127-full-1');work=Path('/mnt/lfs/sources/phase2/work/polkit-full-1');log=Path('/var/log/toddy/phase2')
    assert (source/'toddy-build.sh').read_bytes()==(root/'scripts/build/phase2/polkit-full-build.sh').read_bytes()
    assert (source/'toddy-probe.c').read_bytes()==(root/'scripts/build/phase2/polkit-strict-subject-probe.c').read_bytes()
    patch=json.loads((root/'config/phase2/polkit-patches.lock.json').read_text());prepared=json.loads((source/'toddy-prepared.json').read_text())['source_patches'][0]
    for name in ['source_sha256','source_file','before_sha256','after_sha256','patch_file','patch_sha256']:assert prepared[name]==patch[name]
    assert digest(source/patch['source_file'])==patch['after_sha256'] and digest(root/patch['patch_file'])==patch['patch_sha256']
    assert (log/'polkit-full-1.exit').read_text().strip()=='0'
    stage=json.loads((work/'stage-results.json').read_text());assert stage['compile_exit']==stage['stage_exit']==0
    assert len(stage['original_tests'])==5 and len(stage['artifacts'])==58
    for base,key in [(work/'compile','artifacts'),(work/'stage','stage_sha256')]:
        for name,sha in stage[key].items():assert digest(base/name)==sha
    assert set(stage['stage_sha256'])=={str(p.relative_to(work/'stage')) for p in (work/'stage').rglob('*') if p.is_file() and not p.is_symlink()}
    acceptance=json.loads((log/'polkit-standard-native-acceptance-1.json').read_text());assert acceptance['state']=='native-standard-helper-qualified'
    assert validate(acceptance['proofs'])==acceptance['summary']
    for virtual,sha in acceptance['summary']['helpers'].items():assert digest(work/'stage'/virtual.lstrip('/'))==sha
    # Fresh parent installation only: inspect uncertain prior writes separately.
    for filename,column in [('passwd',2),('group',2)]:
        rows=[s.split(':') for s in (Path('/mnt/lfs/etc')/filename).read_text().splitlines()]
        assert not any(r[0]=='polkitd' or r[column]=='27' for r in rows),'Reconcile service account before fresh transaction'
