#!/usr/bin/env python3
"""Verify frozen native report inputs and import immutable qualification metadata."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

import phase2_vm

ROOT=phase2_vm.ROOT


def main():
    number=int(sys.argv[1]);assert 1<=number<=99
    context=ROOT/'.local/phase2'/('native-bwrap-runtime-'+str(number))
    state=json.loads((context/'result.json').read_text())
    assert state['phase']=='native-report-recorded' and state['native_selected_passed'] and state['backing_unchanged']
    current=json.loads(subprocess.check_output(['docker','inspect',state['container_id']],text=True))[0]
    assert not current['State']['Running'] and current['State']['ExitCode']==0
    assert (current['Config'].get('Labels') or {}).get('toddy.boot-test')==state['run_id']
    report=json.loads((context/'native-report.json').read_text());reports=[(number,report,state)]
    assert re.fullmatch(r'[a-f0-9]{40}',state['commit'])
    def frozen(path):
        return subprocess.check_output(['git','show',state['commit']+':'+path],cwd=ROOT,text=True)
    consumer=frozen('scripts/build/phase2/bubblewrap-probe.py')
    body=frozen('scripts/host/phase2-native-bwrap-probe.py')
    assert body.count('CONSUMER_SOURCE = None')==1
    body=body.replace('CONSUMER_SOURCE = None','CONSUMER_SOURCE = '+repr(consumer))
    reused=None
    if report.get('reused_native_proof') is not None:
        previous_name=state['cold_followup_of'];assert re.fullmatch(r'native-bwrap-runtime-[0-9]+',previous_name)
        old_context=context.parent/previous_name;old_state=json.loads((old_context/'result.json').read_text())
        old=json.loads((old_context/'native-report.json').read_text())
        reused_number=int(previous_name.rsplit('-',1)[1]);reports.append((reused_number,old,old_state))
        reused=[{k:r[k] for k in ['name','exit']} for r in old['runs'] if r['name'] in ['test-specifying-pidns.sh','test-specifying-userns.sh']]
        assert len(reused)==2 and all(r['exit']==0 for r in reused)
        proof={'kernel':old['kernel'],'binary_sha256':old['binary_sha256'],'runs':reused,'report_sha256':old_state['summary']['report_sha256']}
        assert proof==report['reused_native_proof']
        body=body.replace('REUSED_NATIVE_PROOF = None','REUSED_NATIVE_PROOF = '+repr(proof))
    assert hashlib.sha256(body.encode()).hexdigest()==state['probe_sha256']
    compact={'kernel':report['kernel'],'binary_sha256':report['binary_sha256'],
             'native_report_sha256':state['summary']['report_sha256'],
             'native_report_file':'bubblewrap-native-runtime-'+str(number)+'.json',
             'native_probe_sha256':state['probe_sha256'],
             'consumer_source_sha256':hashlib.sha256(consumer.encode()).hexdigest(),
             'existing_compiled_elf_files_unchanged':report['existing_compiled_elf_files_unchanged']}
    if reused is not None:
        compact.update(reused_report_sha256=old_state['summary']['report_sha256'],reused_report_file='bubblewrap-native-runtime-'+str(reused_number)+'.json')
    for index,r,s in reports:
        data=json.dumps(r,sort_keys=True).encode();expected=s['summary']['report_sha256']
        assert hashlib.sha256(data).hexdigest()==expected
        code='''from pathlib import Path
import fcntl,hashlib,json,os,socket,subprocess
assert os.geteuid()==0 and socket.gethostname()=='toddy-builder'
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
'''+f'data={data!r}\nexpected={expected!r}\nindex={index!r}\n'+'''
assert hashlib.sha256(data).hexdigest()==expected
p=Path('/var/log/toddy/phase2')/('bubblewrap-native-runtime-'+str(index)+'.json')
if p.exists():assert p.read_bytes()==data+b'\\n','Existing report drift; never overwrite'
else:
 with p.open('xb') as f:f.write(data+b'\\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'report':p.name,'sha256':expected,'verified':True}))
'''
        done=subprocess.run(phase2_vm.ssh_args()+['python3 -'],input=code.encode(),capture_output=True)
        done.check_returncode();print(done.stdout.decode().strip())
    destination=context/'qualification-input.json'
    text=json.dumps(compact,indent=2)+'\n'
    if destination.exists():assert destination.read_text()==text
    else:destination.write_text(text)
    print(json.dumps({'qualification_input':str(destination),'native_report_sha256':compact['native_report_sha256']}))


if __name__=='__main__':main()
