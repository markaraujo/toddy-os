"""Recheck affected LLVM Support units from the book's normal build directory."""
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

SUPPORT='LLVM-Unit :: Support/./SupportTests/'
RELATIVE=SUPPORT+'VFSFromYAMLTest/RelativePaths'


def validate_original(original):
    failed=[r for r in original if r['code']!='PASS']
    assert len(failed)==1 and failed[0]['code']=='FAIL' and failed[0]['name']==RELATIVE
    assert 'Which is: "elative/path.h"' in failed[0]['output'], 'Unknown original failure'
    affected={r['name'] for r in original if r['name'].startswith(SUPPORT)}
    assert affected and len({r['name'] for r in original})==len(original)
    return affected


def merge_support_results(original, corrected):
    affected=validate_original(original)
    replacements={r['name']:r for r in corrected}
    assert affected and set(replacements)==affected and len(replacements)==len(corrected)
    assert all(r['code']=='PASS' for r in corrected), 'Affected native cases still failing'
    combined=[replacements.get(r['name'],r) for r in original]
    assert len({r['name'] for r in combined})==len(combined)
    assert all(r['code']=='PASS' for r in combined)
    return combined


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def binary_inputs():
    paths={Path('/build/compile/lib/libLLVM.so.22.1')}
    for directory in ['bin','unittests']:
        for path in (Path('/build/compile')/directory).rglob('*'):
            if path.is_file() and not path.is_symlink():
                with path.open('rb') as stream:header=stream.read(4)
                if header==b'\x7fELF':paths.add(path)
    return {str(p):digest(p) for p in sorted(paths)}


def main():
    import psutil
    import resource
    assert os.getuid()==101 and psutil.__version__=='7.2.2'
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    work=Path('/build');root=work/'critical-tests-recovery-4'
    assert not root.exists() and not Path('/stage/usr').exists(),'Reconcile prior stage/recovery'
    assert json.loads((work/'compile-result.json').read_text())['version']=='22.1.8'
    stat=os.statvfs(work);assert stat.f_bavail*stat.f_frsize>=24*1024**3
    original_path=work/'critical-tests-resume/llvm-unit.json'
    original=json.loads(original_path.read_text())['tests']
    # Refuse any new failure before dispatching the specifically affected group.
    validate_original(original)
    root.mkdir();before=binary_inputs();(root/'binary-inputs.json').write_text(json.dumps(before,indent=2)+'\n')
    os.chdir('/build/compile')
    assert os.getcwd()=='/build/compile'
    results=[]

    def run(name,path,extra=()):
        stat=os.statvfs(work);assert stat.f_bavail*stat.f_frsize>=16*1024**3
        report=root/(name+'.json');log=root/(name+'.log')
        assert not report.exists() and not log.exists()
        with log.open('xb') as output:
            result=subprocess.run(['/build/compile/bin/llvm-lit','-sv','-j4','--timeout=120','--output',str(report),*extra,path],stdout=output,stderr=subprocess.STDOUT)
        assert report.exists(),name+' produced no terminal report'
        tests=json.loads(report.read_text())['tests'];counts=dict(collections.Counter(r['code'] for r in tests))
        row={'name':name,'exit':result.returncode,'lit_entries':len(tests),'counts':counts,'report_sha256':digest(report),'log_sha256':digest(log)}
        print(json.dumps(row),flush=True)
        assert result.returncode==0 and tests and counts.get('PASS',0)>0,name+' failed or empty'
        assert set(counts)<={'PASS','XFAIL','UNSUPPORTED'}
        return row,tests

    support_row,corrected=run('llvm-unit-support','/build/compile/test/Unit',('--filter',re.escape(SUPPORT)))
    combined=merge_support_results(original,corrected)
    unit_recovery={'original_report_sha256':digest(original_path),'affected_report_sha256':support_row['report_sha256'],
                   'original_native_exit':1,'affected_native_exit':0,'cwd':os.getcwd(),
                   'reused_passed_cases':len(original)-len(corrected),'affected_passed_cases':len(corrected),
                   'original_failure_preserved':RELATIVE}
    report=root/'llvm-unit.json'
    report.write_text(json.dumps({'kind':'derived qualification of preserved native reports, not a new full-suite run','qualification':unit_recovery,'tests':combined},indent=2)+'\n')
    results.append({'name':'llvm-unit','qualification_exit':0,'original_native_exit':1,'affected_native_exit':0,
                    'lit_entries':len(combined),'counts':{'PASS':len(combined)},'report_sha256':digest(report)})
    suites=[('clang-unit','/build/compile/tools/clang/test/Unit'),
            ('llvm-transforms','/src/llvm/test/Transforms'),('llvm-x86','/src/llvm/test/CodeGen/X86'),
            ('llvm-execution-engine','/src/llvm/test/ExecutionEngine'),
            ('clang-codegen','/src/clang/test/CodeGen'),('clang-codegen-cxx','/src/clang/test/CodeGenCXX')]
    for name,path in suites:
        row,_=run(name,path);results.append(row)
        (root/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    regressions=[r for r in json.loads((root/'llvm-x86.json').read_text())['tests'] if r['name'].endswith('select-of-load-poison.ll')]
    assert len(regressions)==1 and regressions[0]['code']=='PASS'
    after={p:digest(Path(p)) for p in before};assert before==after,'Compiler/test binary changed'
    (root/'qualified.json').write_text(json.dumps({'scope':'ADR0121 critical suites with ADR0124 affected Support cwd correction; original raw unit failure retained, other unit cases reused, no full cross-target/compiler-rt matrix',
        'suites':results,'unit_recovery':unit_recovery,'binary_inputs':before,'binaries_unchanged':True,'required_poison_select_regression':'PASS'},indent=2)+'\n')
    stat=os.statvfs(work);assert stat.f_bavail*stat.f_frsize>=20*1024**3
    subprocess.run(['cmake','--install','/build/compile'],env=dict(os.environ,DESTDIR='/stage'),check=True)
    config=Path('/stage/etc/clang');config.mkdir(parents=True)
    for name in ['clang.cfg','clang++.cfg']:(config/name).write_text('-fstack-protector-strong\n')
    assert all((Path('/stage/usr/bin')/p).exists() for p in ['clang','FileCheck','llvm-config'])


if __name__=='__main__':main()
