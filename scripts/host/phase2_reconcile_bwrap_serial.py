#!/usr/bin/env python3
"""Recover one split protocol marker only when the complete advertised hash matches."""
import base64
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zlib

import phase2_vm

root=phase2_vm.ROOT/'.local/phase2/native-bwrap-runtime-3'
record=root/'result.json';state=json.loads(record.read_text())
assert state['phase']=='native-stopped' and not state['container_final_state']['Running']
assert state['container_final_state']['ExitCode']==0
info=json.loads(subprocess.check_output(['docker','inspect',state['container_id']],text=True))[0]
assert not info['State']['Running'] and (info['Config'].get('Labels') or {}).get('toddy.boot-test')==state['run_id']
assert phase2_vm.backing_identity(phase2_vm.WORK/'lfs-target.qcow2')==state['source_identity']
assert not subprocess.check_output(['docker','ps','-q','--filter','name=^/'+phase2_vm.NAME+'$'],text=True).strip()
serial=root/'serial.log';data=serial.read_bytes();lines=data.decode().splitlines()
chunks={};summaries=[];recovery=[]
for i,line in enumerate(lines):
    marker='TODDY_B02_RUNTIME_DATA '
    if marker in line:
        number,value=line.split(marker,1)[1].split(' ',1)
        index=int(number);assert index not in chunks or chunks[index]==value;chunks[index]=value
    if line.startswith('DY_B02_RUNTIME_DATA '):
        # Kernel printk split the marker after 'TOD', not any payload bytes.
        assert i>0 and re.search(r'python3\[\d+\]: TOD\[\s*[0-9.]+\] python3 \(\d+\) used greatest stack depth:',lines[i-1])
        number,value=line.removeprefix('DY_B02_RUNTIME_DATA ').split(' ',1)
        index=int(number);assert index==1 and index not in chunks and len(value)==1024
        assert re.fullmatch(r'[A-Za-z0-9+/=]+',value)
        chunks[index]=value;recovery.append({'index':index,'payload_bytes_changed':0,'reason':'Exact TOD + DY marker split by kernel stack-depth printk; full payload line retained'})
    if 'TODDY_B02_RUNTIME_RESULT ' in line:
        summaries.append(json.loads(line.split('TODDY_B02_RUNTIME_RESULT ',1)[1]))
assert len(recovery)==1 and summaries and all(s==summaries[0] for s in summaries)
summary=summaries[0];assert set(chunks)==set(range(summary['chunks'])) and summary['all_selected_exits_zero'] is True
raw=zlib.decompress(base64.b64decode(''.join(chunks[i] for i in range(len(chunks))),validate=True))
assert len(raw)<4*1024**2 and hashlib.sha256(raw).hexdigest()==summary['report_sha256']
report=json.loads(raw);assert report['kernel']=='7.1.8-toddy'
assert len(report['runs'])==2 and all(r['exit']==0 for r in report['runs'])
assert {r['name'] for r in report['runs']}=={'namespace-consumer','test-run.sh'}
assert len(report['reused_native_proof']['runs'])==2 and all(r['exit']==0 for r in report['reused_native_proof']['runs'])
assert report['existing_compiled_elf_files_unchanged']==11
assert not (root/'result-before-serial-reconcile.json').exists()
(root/'result-before-serial-reconcile.json').write_bytes(record.read_bytes())
(root/'native-report.json').write_text(json.dumps(report,indent=2)+'\n')
state.update(phase='native-report-recorded',summary=summary,native_selected_passed=True,backing_unchanged=True,
             serial_reconciliation={'serial_sha256':hashlib.sha256(data).hexdigest(),'recovered_markers':recovery,'verified_full_report_sha256':summary['report_sha256'],'native_tests_replayed':0,'original_controller_parser_failure_retained':True},
             builder_restart='pending reconciliation; never replay native3')
record.write_text(json.dumps(state,indent=2)+'\n')
print(json.dumps({'native_selected_passed':True,'native_kernel':report['kernel'],'selected_runs':[{k:r[k] for k in ['name','exit']} for r in report['runs']],
                  'reused_native_runs':report['reused_native_proof']['runs'],'existing_compiled_elf_files_unchanged':11,'marker_recoveries':recovery,'full_report_sha256':summary['report_sha256']}))
