"""Verify staged editor bytes and headless checks; never imply GUI acceptance."""
from pathlib import Path
import hashlib,json


def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def qualify(root):
    s=Path('/mnt/lfs/sources/phase2/inputs/gnome-text-editor-50.1');w=Path('/mnt/lfs/sources/phase2/work/gnome-text-editor-1');l=Path('/var/log/toddy/phase2')
    p=json.loads((s/'toddy-prepared.json').read_text());assert p['source_sha256']=='f68036b09d378faa883bfe936e479c6ff37027c2ffed101daf912df70c51d0e6' and not p['source_patches']
    assert digest(s/'toddy-build.sh')==p['recipe_sha256']=='164116bf1010e79148546afa81fac2317938e66d48088d8ae83912bbe98d17fb'
    assert (l/'gnome-text-editor-1.exit').read_text().strip()=='1' and (l/'gnome-text-editor-metadata-2.exit').read_text().strip()=='0'
    assert json.loads((l/'gnome-text-editor-metadata-2.job.json').read_text())['command'][-1]==(root/'scripts/build/phase2/gnome-text-editor-resume-metadata.sh').read_text()
    r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
    assert len(r['original_tests'])==1 and r['original_tests'][0]['result']=='OK' and r['original_tests'][0]['returncode']==0
    registered=r['original_registered_tests'];assert len(registered)==1 and registered[0]['name']=='Validate appstream file' and '--no-net' in registered[0]['cmd']
    assert r['consumer']['editorconfig_enabled'] and r['consumer']['graphical_editor_tested'] is False
    assert r['consumer']['version']==(w/'actual-version.log').read_text() and 'Text Editor 50.1' in r['consumer']['version']
    for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
        actual={str(p.relative_to(w/base)):digest(p) for p in (w/base).rglob('*') if p.is_file() and not p.is_symlink() and (key!='artifacts' or p.open('rb').read(4)==b'\x7fELF')}
        assert actual and actual==r[key]
    return r
