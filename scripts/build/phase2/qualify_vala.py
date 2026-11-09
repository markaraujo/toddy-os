"""Require original compiler results and generated native semantic/refusal checks."""
from pathlib import Path
import hashlib,json,re
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
    source=Path('/mnt/lfs/sources/phase2/inputs/vala-0.56.19');work=Path('/mnt/lfs/sources/phase2/work/vala-1');log=Path('/var/log/toddy/phase2')
    assert digest(source/'toddy-build.sh')=='4d20aed2a1783bc5d60a46adc0162d7f0cee146dcc490b3e6801f63b4411929b'
    old=(source/'toddy-build.sh').read_text()
    assert old.replace('LD_LIBRARY_PATH=/stage/usr/lib python3','LD_LIBRARY_PATH=/stage/usr/lib:/stage/usr/lib/vala-0.56 python3')==(root/'scripts/build/phase2/vala-build.sh').read_text()
    assert (source/'toddy-probe.py').read_bytes()==(root/'scripts/build/phase2/vala-probe.py').read_bytes()
    prefix=['/bin/bash',str(root/'scripts/build/phase2/isolated.sh'),'--loopback',str(source),str(work)]
    for name,command,exitcode in [('vala-1',['bash','/src/toddy-build.sh'],'1'),('vala-consumer-2',['python3','-c',(root/'scripts/build/phase2/vala_consumer_finish.py').read_text()],'0')]:
        assert (log/(name+'.exit')).read_text().strip()==exitcode
        assert json.loads((log/(name+'.job.json')).read_text())['command']==prefix+command
    result=json.loads((work/'stage-results.json').read_text());assert result['compile_exit']==result['stage_exit']==0
    tests={}
    for f in (work/'compile').rglob('*.trs'):
        m=re.search(r'^:test-result: (\S+)$',f.read_text(),re.M);assert m and m[1]=='PASS'
        tests[str(f.relative_to(work/'compile'))]=m[1]
    assert len(tests)==len(result['original_tests'])==1435
    assert tests=={t['name']:t['result'] for t in result['original_tests']}
    assert result['original_ELFs_and_stage_unchanged'] and result['original_records_unchanged']
    assert result['consumer']=={'compiler_version':'Vala 0.56.19','actual_generated_GObject_UTF8_signal_error_ABI':True,'invalid_typed_source_refused':True,'no_rejected_executable':True,'post_refusal_recovery_cycles':[{'cycle':0,'compile_exit':0,'generated_native_exit':0},{'cycle':1,'compile_exit':0,'generated_native_exit':0}],'real_credentials_used':False}
    for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
        for name,sha in result[key].items():assert digest(work/base/name)==sha
    return result
