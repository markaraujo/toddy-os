"""Bind original TLS/proxy results and the consumer-only standard PEM correction."""
from pathlib import Path
import hashlib,json
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
    source=Path('/mnt/lfs/sources/phase2/inputs/glib-networking-2.80.1');work=Path('/mnt/lfs/sources/phase2/work/glib-networking-1');log=Path('/var/log/toddy/phase2')
    assert (source/'toddy-build.sh').read_bytes()==(root/'scripts/build/phase2/glib-networking-build.sh').read_bytes()
    assert digest(source/'toddy-probe.c')=='6c7b917684f956fa15ef94f01aebc551e7cf6c981c7a660ab299b1e4a8626acd'
    prefix=['/bin/bash',str(root/'scripts/build/phase2/isolated.sh'),'--loopback',str(source),str(work)]
    for n,code,exitcode in [('glib-networking-1',['bash','/src/toddy-build.sh'],'1'),('glib-networking-tls-2',['python3','-c',(root/'scripts/build/phase2/glib_networking_finish.py').read_text()],'1'),('glib-networking-consumer-3',['python3','-c',(root/'scripts/build/phase2/glib_networking_consumer.py').read_text(),(root/'scripts/build/phase2/glib-networking-probe.c').read_text()],'0')]:
        assert (log/(n+'.exit')).read_text().strip()==exitcode
        assert json.loads((log/(n+'.job.json')).read_text())['command']==prefix+code
    assert (work/'consumer-3.c').read_bytes()==(root/'scripts/build/phase2/glib-networking-probe.c').read_bytes()
    initial=[json.loads(s) for s in (work/'initial-testlog-1.json').read_text().splitlines() if s.strip()]
    remaining=[json.loads(s) for s in (work/'remaining-testlog-2.json').read_text().splitlines() if s.strip()]
    assert len(initial)==6 and sum(t['result']=='OK' for t in initial)==3 and sum(t['result']=='FAIL' for t in initial)==3
    assert {t['name'] for t in remaining}=={'glib-networking:'+n for n in ['file-database-gnutls','connection-gnutls','connection-gnutls-tls1.2']}
    tests=[t for t in initial if t['result']=='OK']+remaining
    assert len(tests)==6 and all(t['result']=='OK' and t['returncode']==0 for t in tests)
    result=json.loads((work/'stage-results.json').read_text());assert result['compile_exit']==result['stage_exit']==0
    assert result['original_tests']==[{k:t[k] for k in ['name','result','returncode']} for t in tests]
    assert result['prior_ELFs_unchanged'] and result['public_trust_readonly'] and result['stage_unchanged_by_consumer_correction']
    assert result['consumer']=={'actual_GnuTLS_GIO_backend':True,'default_installed_factory_root_verified':True,'malformed_certificate_refused':True,'post_refusal_recovery_cycles':2,'real_credentials_used':False}
    for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
        for name,sha in result[key].items():assert digest(work/base/name)==sha
    return result
