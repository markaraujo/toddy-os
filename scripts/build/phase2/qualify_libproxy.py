"""Require all enabled original proxy/PAC drivers and actual public API lifecycle."""
from pathlib import Path
import hashlib,json
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
    source=Path('/mnt/lfs/sources/phase2/inputs/libproxy-0.5.12');work=Path('/mnt/lfs/sources/phase2/work/libproxy-1');log=Path('/var/log/toddy/phase2')
    for a,b in [('toddy-build.sh','libproxy-build.sh'),('toddy-probe.c','libproxy-probe.c')]:assert (source/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
    assert (log/'libproxy-1.exit').read_text().strip()=='0'
    assert json.loads((log/'libproxy-1.job.json').read_text())['command']==['/bin/bash',str(root/'scripts/build/phase2/isolated.sh'),'--loopback',str(source),str(work),'bash','/src/toddy-build.sh']
    r=json.loads((work/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
    original=[json.loads(s) for s in (work/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
    assert len(original)==5 and all(t['result']=='OK' and t['returncode']==0 for t in original)
    assert r['original_tests']==[{k:t[k] for k in ['name','result','returncode']} for t in original]
    assert {t['name'] for t in original}=={'libproxy:'+n for n in ['Libproxy test','PX Manager test','Config Environment test','Config sysconfig test','Config GNOME test']}
    assert r['consumer']=={'public_direct_resolution':True,'malformed_URI_safe_direct_fallback':True,'bypass_and_post_fallback_recovery':True,'boxed_copy_lifetime':True,'lifecycle_cycles':2,'network_requests_sent':False}
    for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
        for name,sha in r[key].items():assert digest(work/base/name)==sha
    return r
