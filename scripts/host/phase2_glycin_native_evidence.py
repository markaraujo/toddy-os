#!/usr/bin/env python3
"""Verify frozen native probe payloads and import immutable Glycin test reports."""
import ast
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import zlib

import phase2_vm
from phase2_native_glycin import compressed_payload

ROOT=phase2_vm.ROOT


def verify_probe(state,report):
    command=state['command'];prefix='type=11,value=io.systemd.credential.binary:toddy.boot-probe='
    payloads=[x[len(prefix):] for x in command if x.startswith(prefix)]
    assert len(payloads)==1
    payload=base64.b64decode(payloads[0],validate=True)
    if 'payload_sha256' in state:
        assert hashlib.sha256(payload).hexdigest()==state['payload_sha256']
        tree=ast.parse(payload)
        calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
               and isinstance(n.func.value,ast.Name) and n.func.value.id=='base64' and n.func.attr=='b64decode']
        assert len(calls)==1
        packed=base64.b64decode(ast.literal_eval(calls[0].args[0]),validate=True)
        decoder=zlib.decompressobj();raw=decoder.decompress(packed,65537)
        assert len(raw)<=65536 and decoder.eof and not decoder.unused_data
        assert compressed_payload(raw)==payload
    else:raw=payload
    assert hashlib.sha256(raw).hexdigest()==state['probe_sha256']
    source=raw.decode('utf-8')
    def frozen(path):return subprocess.check_output(['git','show',state['commit']+':'+path],cwd=ROOT,text=True)
    template=frozen('scripts/host/phase2-native-glycin-probe.py')
    expected={'CONSUMER_SOURCE':frozen('scripts/build/phase2/glycin-native-consumer.py')}
    if 'MIME_COMPAT_SOURCE = None' in template:
        expected['MIME_COMPAT_SOURCE']=frozen('scripts/build/phase2/glycin_mime_compat.py')
        expected['REUSED_NATIVE_PROOF']=report.get('reused_native_proof')
    if 'FIXTURE_NAME =' in template:expected['FIXTURE_NAME']='glycin-2' if report.get('source_compatibility') else 'glycin-1'
    actual={n.targets[0].id:n for n in ast.parse(source).body
            if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)}
    original={n.targets[0].id:n for n in ast.parse(template).body
              if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)}
    replacements=[]
    for name,value in expected.items():
        assert ast.literal_eval(actual[name].value)==value
        replacements.append((name+' = '+ast.get_source_segment(template,original[name].value),
                             name+' = '+ast.get_source_segment(source,actual[name].value)))
    for old,new in replacements:
        assert template.count(old)==1;template=template.replace(old,new)
    assert template.encode()==raw,'Frozen native probe differs outside exact verified inserted literals'


def main():
    reports={};states={}
    for number in [1,4,5]:
        context=ROOT/'.local/phase2'/('native-glycin-runtime-'+str(number))
        state=json.loads((context/'result.json').read_text());report=json.loads((context/'native-report.json').read_text())
        assert state['phase']=='native-report-recorded' and state['backing_unchanged']
        container=json.loads(subprocess.check_output(['docker','inspect',state['container_id']],text=True))[0]
        assert not container['State']['Running'] and container['State']['ExitCode']==0
        assert (container['Config'].get('Labels') or {}).get('toddy.boot-test')==state['run_id']
        assert hashlib.sha256(json.dumps(report,sort_keys=True).encode()).hexdigest()==state['summary']['report_sha256']
        verify_probe(state,report);reports[str(number)]=report;states[str(number)]=state
    assert states['5']['native_selected_passed'] and all(r['exit']==0 for r in reports['5']['runs'])
    assert reports['5']['stage_file_hashes']==reports['4']['stage_file_hashes']
    assert reports['5']['reused_native_proof']['report_sha256']==states['1']['summary']['report_sha256']
    assert reports['5']['reused_native_proof']['candidate_report_sha256']==states['4']['summary']['report_sha256']
    proof={'scope':'Native Glycin selected original tests; retained failure/recovery chain, no GNOME/G2 acceptance',
           'reports':{n:{'file':'glycin-native-runtime-'+n+'.json','sha256':s['summary']['report_sha256'],
                         'probe_sha256':s['probe_sha256'],'commit':s['commit']} for n,s in states.items()},
           'baseline_fixture_payload_sha256':states['1']['accepted']['fixture_payload_sha256'],
           'candidate_fixture_payload_sha256':states['5']['accepted']['fixture_payload_sha256'],
           'kernel':'7.1.8-toddy','all_selected_qualified':True}
    code='''from pathlib import Path
import fcntl,hashlib,json,os,subprocess
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
f=open('/var/log/toddy/build/build.lock','a');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
def write_once(path,data):
 if path.exists():assert path.read_bytes()==data,'Existing proof differs; never overwrite'
 else:
  with path.open('xb') as out:out.write(data);out.flush();os.fsync(out.fileno())
'''+f'reports={reports!r}\nproof={proof!r}\n'+'''
for n,r in reports.items():
 data=json.dumps(r,sort_keys=True).encode();row=proof['reports'][n]
 assert hashlib.sha256(data).hexdigest()==row['sha256']
 write_once(Path('/var/log/toddy/phase2')/row['file'],data+b'\\n')
write_once(Path('/var/log/toddy/phase2/glycin-native-qualification.json'),json.dumps(proof,sort_keys=True).encode()+b'\\n')
print(json.dumps({'reports_imported':len(reports),'qualified':True}))
'''
    done=subprocess.run(phase2_vm.ssh_args()+['python3 -'],input=code.encode(),capture_output=True)
    print(done.stdout.decode());print(done.stderr.decode());done.check_returncode()
    path=ROOT/'.local/phase2/glycin-native-qualification.json'
    if path.exists():assert json.loads(path.read_text())==proof
    else:path.write_text(json.dumps(proof,indent=2)+'\n')


if __name__=='__main__':main()
