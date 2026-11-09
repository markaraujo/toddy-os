"""Require exact staged UCD bytes, frozen terms and actual scalar/range checks."""
from pathlib import Path
import hashlib,json
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
    source=Path('/mnt/lfs/sources/phase2/inputs/unicode-ucd-17.0.0');work=Path('/mnt/lfs/sources/phase2/work/unicode-ucd-1');log=Path('/var/log/toddy/phase2')
    assert (log/'unicode-ucd-1.exit').read_text().strip()=='0'
    assert json.loads((log/'unicode-ucd-1.job.json').read_text())['command']==['/bin/bash',str(root/'scripts/build/phase2/isolated.sh'),str(source),str(work),'bash','/src/toddy-build.sh']
    for a,b in [('toddy-build.sh','unicode-ucd-build.sh'),('toddy-probe.py','unicode-ucd-probe.py')]:assert (source/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
    lock=json.loads((root/'config/phase2/sources.lock.json').read_text())['components']
    data=next(r for r in lock if r['name']=='unicode-ucd');license=next(r for r in lock if r['name']=='unicode-data-license')
    assert data['version']=='17.0.0' and license['version']=='3.0'
    assert digest(Path('/mnt/lfs/sources')/data['filename'])==data['sha256']
    assert digest(Path('/mnt/lfs/sources')/license['filename'])==license['sha256']==digest(source/'Unicode-License-3.0.txt')
    assert (source/'Unicode-License-3.0.txt').read_text().startswith('UNICODE LICENSE V3')
    r=json.loads((work/'stage-results.json').read_text());assert r['stage_exit']==0
    actual={str(f.relative_to(source/'ucd')):digest(f) for f in (source/'ucd').rglob('*') if f.is_file()}
    assert actual==r['source_manifest'] and len(actual)==71
    for name,sha in r['stage_sha256'].items():assert digest(work/'stage'/name)==sha
    assert r['consumer']=={'version':'17.0.0','scalar_records':40575,'sorted_valid_scalar_fields':True,'block_ranges':346,'nonoverlapping_blocks':True,'Latin_Portuguese_emoji_metadata':True,'UTF8_names':True,'rendering_or_input_claimed':False}
    assert not Path('/mnt/lfs/usr/share/unicode/ucd').exists(),'Inspect existing data before ownership promotion'
    return r
