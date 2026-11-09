"""Bind retained original protocol results, actual CA repair and native consumer."""
from pathlib import Path
import collections,hashlib,json,re
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
    source=Path('/mnt/lfs/sources/phase2/inputs/gnutls-3.8.13');work=Path('/mnt/lfs/sources/phase2/work/gnutls-1');log=Path('/var/log/toddy/phase2')
    for a,b in [('toddy-build.sh','gnutls-build.sh'),('toddy-probe.c','gnutls-probe.c')]:
        assert (source/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
    prefix=['/bin/bash',str(root/'scripts/build/phase2/isolated.sh'),'--loopback',str(source),str(work)]
    for name,script,exitcode in [('gnutls-1',None,'2'),('gnutls-remaining-2','gnutls_remaining.py','2'),('gnutls-certificates-3','gnutls_certificates.py','0'),('gnutls-stage-5','gnutls_finish.py','0')]:
        assert (log/(name+'.exit')).read_text().strip()==exitcode
        command=['bash','/src/toddy-build.sh'] if script is None else ['python3','-c',(root/'scripts/build/phase2'/script).read_text()]
        assert json.loads((log/(name+'.job.json')).read_text())['command']==prefix+command
    result=json.loads((work/'stage-results.json').read_text());assert result['compile_exit']==result['stage_exit']==0
    tests=[]
    for f in (work/'compile').rglob('*.trs'):
        m=re.search(r'^:test-result: (\S+)$',f.read_text(),re.M);assert m
        tests.append({'name':str(f.relative_to(work/'compile')),'result':m[1]})
    assert len(tests)==len(result['original_tests'])==917
    assert {t['name']:t['result'] for t in tests}=={t['name']:t['result'] for t in result['original_tests']},'Original test names/results changed'
    assert collections.Counter(t['result'] for t in tests)=={'PASS':813,'SKIP':102,'FAIL':2}
    assert {t['name'] for t in tests if t['result']=='FAIL'}=={'src/gl/tests/test-getaddrinfo.trs','tests/trust-store.trs'}
    for name in ['tests/tls13/supported_versions.trs','tests/tls13/anti_replay.trs']:assert {'name':name,'result':'PASS'} in tests
    certificates=(work/'certificates-3-tests-cert-tests.log').read_text()
    listed=re.search(r'^make  (pathlen.sh .*?)$',certificates,re.M)[1].split()
    assert len(listed)==80 and len(set(listed))==73
    assert set(re.findall(r'^PASS: (.+)$',certificates,re.M))==set(listed)
    assert result['original_ELFs_unchanged']
    for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
        for name,sha in result[key].items():assert digest(work/base/name)==sha,name
    assert result['consumer']=={'SHA256_and_AEAD_roundtrip':True,'tampered_tag_refused_and_recovered':True,'actual_password_API_invalid_UTF8_refused':True,'NFC_prior_state_preserved':True,'IDNA2008_conversion':True,'TLS13_priority_and_invalid_priority_refusal':True,'lifecycle_cycles':2,'real_credentials_used':False}
    # Initial missing-root FAIL stays immutable. A separate actual installed-root
    # execution proves the repair; route-dependent DNS is still a B02 gate.
    installed=json.loads((log/'ca-native-installed-consumer.json').read_text())
    step=json.loads(Path('/var/log/toddy/build/b02-ca-native-install.success.json').read_text())
    assert step['recipe_exit']==step['postcheck_exit']==0
    assert installed['original_default_GnuTLS_trust_store_exit']==installed['OpenSSL_default_ISRG_root_exit']==0
    assert installed['anchors']==172 and installed['server_auth_certificates']==121
    return result
