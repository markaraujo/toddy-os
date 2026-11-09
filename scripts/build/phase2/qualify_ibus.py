"""Bind the immutable IBus jobs, scoped corrections and retained native outputs."""
from pathlib import Path
import hashlib,json,re

def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def qualify(root):
    source=Path('/mnt/lfs/sources/phase2/inputs/ibus-1.5.34');work=Path('/mnt/lfs/sources/phase2/work/ibus-1');log=Path('/var/log/toddy/phase2')
    assert digest(source/'toddy-build.sh')=='160a21219c0b11be1cb53c29b256830f502cc9a7a9e4fe2553961548bf6fcc6d'
    assert (source/'toddy-probe.c').read_bytes()==(root/'scripts/build/phase2/ibus-probe.c').read_bytes()
    prepared=json.loads((source/'toddy-prepared.json').read_text())
    assert prepared['source_sha256']=='ff8f511770844203108119727dc8686c29afb286e9cb535e0870f18d40fddbbb'
    expected=[('ibus-1',2,['bash','/src/toddy-build.sh']),('ibus-gtk4-2',1,['python3','-c',(root/'scripts/build/phase2/ibus_finish.py').read_text()]),('ibus-wayland-3',1,['python3','-c',(root/'scripts/build/phase2/ibus_wayland_finish.py').read_text()]),('ibus-link-4',1,['python3','-c',(root/'scripts/build/phase2/ibus_link_finish.py').read_text()]),('ibus-machine-5',0,['python3','-c',(root/'scripts/build/phase2/ibus_machine_finish.py').read_text()])]
    for name,code,command in expected:
        assert (log/(name+'.exit')).read_text().strip()==str(code)
        assert json.loads((log/(name+'.job.json')).read_text())['command']==['/bin/bash',str(root/'scripts/build/phase2/isolated.sh'),str(source),str(work)]+command
    result=json.loads((work/'stage-results.json').read_text());assert result['compile_exit']==result['stage_exit']==0
    names={'src/tests/'+n+'.trs' for n in ['ibus-keynames','ibus-registry','ibus-serializable','ibus-share','ibus-util','ibus-keyval']}|{'bus/test-matchrule.trs'}
    assert {t['name'] for t in result['original_tests']}==names and len(result['original_tests'])==7
    for t in result['original_tests']:
        assert t['result']=='PASS'
        assert re.search(r'^:test-result: PASS$',(work/'source'/t['name']).read_text(),re.M)
        if t['name'].startswith('src/tests/') and not t['name'].endswith('/ibus-share.trs'):
            for suffix in ['.trs','.log']:
                rel=Path(t['name']).with_suffix(suffix)
                assert (work/'source'/rel).read_bytes()==(work/'original-before-5'/rel.name).read_bytes()
    assert ':test-result: FAIL' in (work/'original-before-5/ibus-share.trs').read_text()
    assert 'Unable to load /var/lib/dbus/machine-id' in (work/'original-before-5/ibus-share.log').read_text()
    config=(work/'configure-3.log').read_text()
    assert 'Build XIM agent server        no' in config and 'Build gtk4 immodule           yes' in config
    assert '#define PACKAGE_VERSION "1.5.34-rc2"' in (work/'source/config.h').read_text()
    assert result['consumer']=={'UTF8_serialization_roundtrip':True,'unknown_modifier_refused':True,'valid_key_recovery':True,'cycles':2,'display_or_real_input_tested':False}
    before=json.loads((work/'artifacts-before-5.json').read_text());assert len(before)==177
    assert len(result['artifacts'])==179
    assert set(result['artifacts'])-set(before)=={'client/gtk3/.libs/im-ibus.soT','client/gtk4/.libs/libim-ibus.soT'}
    assert all(result['artifacts'].get(n)==sha for n,sha in before.items())
    for base,key in [('source','artifacts'),('stage','stage_sha256')]:
        for name,sha in result[key].items():assert digest(work/base/name)==sha
    assert len(result['stage_sha256'])==200
    for change in result['source_corrections']:
        assert digest(source/change['path'])==change['before_sha256']
        assert digest(work/'source'/change['path'])==change['after_sha256']
    return result
