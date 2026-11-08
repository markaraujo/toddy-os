#!/bin/bash
# Resume after missing psutil; no compiler or critical dependency rebuild.
set -euo pipefail
[[ $(id -u) == 101 && -f /build/compile-result.json && ! -e /stage/usr ]]
ulimit -c 0
python3 - <<'SPACE'
import os,json
from pathlib import Path
assert json.loads(Path('/build/compile-result.json').read_text())['version']=='22.1.8'
s=os.statvfs('/build');assert s.f_bavail*s.f_frsize>=24*1024**3,'Preserve16GiB plus8GiB critical-test headroom'
SPACE
mkdir /build/critical-tests-resume
python3 - <<'REUSE'
from pathlib import Path
import subprocess,psutil
assert psutil.__version__=='7.2.2'
old=Path('/build/critical-tests')
assert not list(old.glob('*.json')),'Original reports require explicit reconciliation'
assert 'Requires the Python psutil module but it could not be found' in (old/'llvm-unit.log').read_text()
r=subprocess.run(['ninja','-C','/build/compile','-n','UnitTests','ClangUnitTests','llvm-test-depends','clang-test-depends'],capture_output=True,text=True,check=True)
Path('/build/critical-tests-resume/dependency-dry-run.log').write_text(r.stdout+r.stderr)
assert r.stdout.rstrip().endswith('ninja: no work to do.'),'Changed dependency outputs; inspect, do not blindly rebuild'
REUSE
python3 - <<'TESTS'
from pathlib import Path
import collections,hashlib,json,os,subprocess
root=Path('/build/critical-tests-resume');lit='/build/compile/bin/llvm-lit'
suites=[('llvm-unit','/build/compile/test/Unit'),
        ('clang-unit','/build/compile/tools/clang/test/Unit'),
        ('llvm-transforms','/src/llvm/test/Transforms'),
        ('llvm-x86','/src/llvm/test/CodeGen/X86'),
        ('llvm-execution-engine','/src/llvm/test/ExecutionEngine'),
        ('clang-codegen','/src/clang/test/CodeGen'),
        ('clang-codegen-cxx','/src/clang/test/CodeGenCXX')]
results=[]
for name,path in suites:
    s=os.statvfs('/build');assert s.f_bavail*s.f_frsize>=16*1024**3,'Target reserve reached; checkpoint, no next test dispatch'
    report=root/(name+'.json');log=root/(name+'.log')
    assert not report.exists() and not log.exists(),'Reconcile previous critical tests; no replay'
    with log.open('xb') as output:
        result=subprocess.run([lit,'-sv','-j4','--timeout=120','--output',str(report),path],stdout=output,stderr=subprocess.STDOUT)
    if not report.exists():raise RuntimeError(name+' did not produce a terminal test report; see '+str(log))
    data=json.loads(report.read_text());tests=data['tests'];counts=dict(collections.Counter(t['code'] for t in tests))
    row={'name':name,'exit':result.returncode,'lit_entries':len(tests),'counts':counts,
         'report_sha256':hashlib.sha256(report.read_bytes()).hexdigest(),
         'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()}
    results.append(row);(root/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(row),flush=True)
    assert result.returncode==0 and tests and counts.get('PASS',0)>0,name+' failed or empty'
    assert set(counts)<= {'PASS','XFAIL','UNSUPPORTED'},name+' unexpected result requires diagnosis'
# Explicit wrong-code regression from the exact book patch must actually pass.
x86=json.loads((root/'llvm-x86.json').read_text())['tests']
regressions=[t for t in x86 if t['name'].endswith('select-of-load-poison.ll')]
assert len(regressions)==1 and regressions[0]['code']=='PASS'
(root/'qualified.json').write_text(json.dumps({'scope':'ADR0121 selected native compiler/JIT suites only; no full cross-target/compiler-rt matrix','suites':results,'required_poison_select_regression':'PASS'},indent=2)+'\n')
TESTS
python3 - <<'SPACE'
import os
s=os.statvfs('/build');assert s.f_bavail*s.f_frsize>=20*1024**3,'Need staging/package headroom above16GiB reserve'
SPACE
DESTDIR=/stage cmake --install /build/compile
mkdir -p /stage/etc/clang
printf '%s\n' '-fstack-protector-strong' > /stage/etc/clang/clang.cfg
printf '%s\n' '-fstack-protector-strong' > /stage/etc/clang/clang++.cfg
[[ -x /stage/usr/bin/clang && -x /stage/usr/bin/FileCheck && -x /stage/usr/bin/llvm-config ]]
