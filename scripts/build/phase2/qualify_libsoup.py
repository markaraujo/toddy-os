"""Require actual original HTTP/TLS drivers and cancellation/recovery consumer."""
from pathlib import Path
import hashlib,json,re
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
    source=Path('/mnt/lfs/sources/phase2/inputs/libsoup-3.6.6');work=Path('/mnt/lfs/sources/phase2/work/libsoup-1');log=Path('/var/log/toddy/phase2')
    for a,b in [('toddy-build.sh','libsoup-build.sh'),('toddy-probe.c','libsoup-probe.c')]:assert (source/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
    assert (log/'libsoup-1.exit').read_text().strip()=='0'
    job=json.loads((log/'libsoup-1.job.json').read_text())
    assert job['command']==['/bin/bash',str(root/'scripts/build/phase2/isolated.sh'),'--loopback',str(source),str(work),'bash','/src/toddy-build.sh']
    assert job['harness_sha256']==digest(root/'scripts/build/phase2/isolated.sh')
    result=json.loads((work/'stage-results.json').read_text());assert result['compile_exit']==result['stage_exit']==0
    tests=[json.loads(s) for s in (work/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
    assert len(tests)==35 and all(t['result']=='OK' and t['returncode']==0 for t in tests)
    assert result['original_tests']==[{k:t[k] for k in ['name','result','returncode']} for t in tests]
    for name in ['ssl','http2','header-parsing','cookies','session','timeout','redirect','range']:
        assert any(t['name']=='libsoup:'+name+'-test' for t in tests)
    skips=[line for t in tests for line in t.get('stdout','').splitlines() if re.search(r'^(?:ok|not ok).*#\s*SKIP',line,re.I)]
    assert len(skips)==22 and sum('apache is not available' in s for s in skips)==13
    assert sum('ntlm_auth is not available' in s for s in skips)==8
    assert sum('Flaky timing with ASAN enabled' in s for s in skips)==1
    assert result['consumer']=={'actual_HTTP_client_server_roundtrip':True,'precancelled_request_refused':True,'cancelled_request_not_dispatched':True,'post_cancel_recovery_cycles':2,'server_requests':4,'external_network_used':False}
    for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
        for name,sha in result[key].items():assert digest(work/base/name)==sha
    return result
