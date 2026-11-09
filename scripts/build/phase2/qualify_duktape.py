"""Require actual normal/debug embedding and unsupported bytecode before promotion."""
import hashlib,json
from pathlib import Path

def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
    source=Path('/mnt/lfs/sources/phase2/inputs/duktape-2.7.0');work=Path('/mnt/lfs/sources/phase2/work/duktape-1')
    for a,b in [('toddy-build.sh','duktape-build.sh'),('toddy-probe.c','duktape-probe.c')]:assert (source/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
    result=json.loads((work/'stage-results.json').read_text());assert result['compile_exit']==result['stage_exit']==0
    assert len(result['records'])==4
    assert {(r['role'],r['library']) for r in result['records']}=={(a,b) for a in ['consumer','original-hello'] for b in ['duktape','duktaped']}
    for r in result['records']:
        assert r['exit']==0
        if r['role']=='consumer':assert json.loads(r['stdout'])=={'version':20700,'checks':15,'bytecode_load_dump':'unsupported','recovery':True}
        else:assert r['stdout']=='Hello world!\n2+3=5'
    expected=(source/'src/duk_config.h').read_text().replace('#define DUK_USE_BYTECODE_DUMP_SUPPORT','#undef DUK_USE_BYTECODE_DUMP_SUPPORT')
    assert (work/'compile/src/duk_config.h').read_text()==(work/'stage/usr/include/duk_config.h').read_text()==expected
    assert (work/'compile/src/duktape.c').read_bytes()==(source/'src/duktape.c').read_bytes()
    assert (work/'compile/src/duktape.h').read_bytes()==(source/'src/duktape.h').read_bytes()
    assert (work/'compile/Makefile.sharedlibrary').read_text()==(source/'Makefile.sharedlibrary').read_text().replace('-Os','-O2')
    for name,sha in result['stage_sha256'].items():assert digest(work/'stage'/name)==sha
    for name in ['duktape','duktaped']:assert digest(work/'compile'/('lib'+name+'.so.207.20700'))==digest(work/'stage/usr/lib'/('lib'+name+'.so.207.20700'))
