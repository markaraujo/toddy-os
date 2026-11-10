"""Verify original EditorConfig tests and unchanged compiled/staged payload."""
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET


def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def qualify(root):
    source=Path('/mnt/lfs/sources/phase2/inputs/editorconfig-0.12.11')
    work=Path('/mnt/lfs/sources/phase2/work/editorconfig-1')
    prepared=json.loads((source/'toddy-prepared.json').read_text())
    assert prepared['source_sha256']=='0aa80e0c90158c8725c29aa978710e8b1071cc5f4e10184576e718349ea32819'
    assert prepared['extra_source']['sha256']=='6ad790d221748e5d9c90a4c42318775ecf6e2876030f3f428fbdac97bcaca8dc'
    assert prepared['source_patches']==[]
    assert digest(source/'toddy-build.sh')==prepared['recipe_sha256']
    assert (source/'toddy-build.sh').read_bytes()==(root/'scripts/build/phase2/editorconfig-build.sh').read_bytes()
    assert (source/'toddy-probe.py').read_bytes()==(root/'scripts/build/phase2/editorconfig-probe.py').read_bytes()
    assert Path('/var/log/toddy/phase2/editorconfig-1.exit').read_text().strip()=='0'
    result=json.loads((work/'stage-results.json').read_text())
    assert result['compile_exit']==result['stage_exit']==0
    cases=ET.parse(work/'original-tests.xml').getroot().findall('.//testcase')
    assert len(cases)==result['original_ctest_cases']==202
    assert all(not any(t.find(k) is not None for k in ['failure','error','skipped']) for t in cases)
    for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
        actual={str(p.relative_to(work/base)):digest(p) for p in (work/base).rglob('*') if p.is_file() and not p.is_symlink() and (key!='artifacts' or p.open('rb').read(4)==b'\x7fELF')}
        assert actual and actual==result[key]
    assert result['consumer']==json.loads((work/'native-consumer.json').read_text())
    assert result['consumer']['C_API_and_CLI'] and result['consumer']['graphical_editor_tested'] is False
    assert result['scratch_free_bytes']>=256*1024**2
    return result
