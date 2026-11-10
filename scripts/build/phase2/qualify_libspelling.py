"""Bind preserved Libspelling programs/stage to their original test results."""
from pathlib import Path
import hashlib
import json


def digest(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def qualify(root):
    source=Path('/mnt/lfs/sources/phase2/inputs/libspelling-0.4.11')
    work=Path('/mnt/lfs/sources/phase2/work/libspelling-1')
    logs=Path('/var/log/toddy/phase2')
    prepared=json.loads((source/'toddy-prepared.json').read_text())
    assert prepared['source_sha256']=='52e53ec3fba0f604cfd0931e26af7f7241a0d4f0208dd5574f43b3589f6d28b2'
    assert prepared['source_patches']==[]
    assert digest(source/'toddy-build.sh')==prepared['recipe_sha256']=='dac22957acb37eed94860df8a2d6b5d4ed2ad19639ac9bef2b0ca975de833ffc'
    assert (source/'toddy-probe.py').read_bytes()==(root/'scripts/build/phase2/libspelling-probe.py').read_bytes()
    assert (logs/'libspelling-1.exit').read_text().strip()=='1'
    assert (logs/'libspelling-options-2.exit').read_text().strip()=='0'
    assert json.loads((logs/'libspelling-options-2.job.json').read_text())['command'][-1]==(root/'scripts/build/phase2/libspelling-resume-options.sh').read_text()
    r=json.loads((work/'stage-results.json').read_text())
    assert r['compile_exit']==r['stage_exit']==0
    assert len(r['original_tests'])==4
    assert [t['name'] for t in r['original_tests']]==['libspelling:test-cursor','libspelling:test-engine','libspelling:test-job','libspelling:test-region']
    assert [t['stdout'].count('\nok ') for t in r['original_tests']]==[4,2,2,13]
    assert all(t['result']=='OK' and t['returncode']==0 for t in r['original_tests'])
    options={o['name']:o['value'] for o in json.loads((work/'compile/meson-info/intro-buildoptions.json').read_text())}
    assert options['vapi'] is False and options['introspection']==options['enchant']=='enabled'
    for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
        actual={str(p.relative_to(work/base)):digest(p) for p in (work/base).rglob('*') if p.is_file() and not p.is_symlink() and (key!='artifacts' or p.open('rb').read(4)==b'\x7fELF')}
        assert actual and actual==r[key]
    for n,sha in json.loads((work/'before-options-2.json').read_text()).items():
        assert digest(work/'compile'/n)==sha
    assert r['consumer']==json.loads((work/'native-consumer.json').read_text())
    assert r['consumer']['namespace']=='Spelling1' and r['consumer']['graphical_widget_tested'] is False
    # Historical collector prose retained an obsolete Vala label. Actual Meson
    # options and payload are authoritative; preserve original bytes and annotate.
    r['original_collector_scope']=r['scope']
    r['scope']='Libspelling0.4.11 Enchant/Aspell English, four original programs/21cases, staged Spelling1 GI; introspection/enchant enabled, optional Vala/docs/profiler disabled. No graphical adapter/editor acceptance.'
    r['scope_label_correction']='Historical collector said Vala enabled; actual intro-buildoptions vapi=false verified. No source/test/stage replay or raw-results rewrite.'
    return r
