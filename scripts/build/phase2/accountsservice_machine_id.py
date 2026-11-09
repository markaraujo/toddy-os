"""Rerun only four original daemon cases with synthetic sandbox machine identity."""
from pathlib import Path
import hashlib,json,os,re,subprocess
assert os.getuid()==101 and Path('/etc/machine-id').read_text()=='00000000000000000000000000000001\n'
p=Path('/build');assert not (p/'stage-results.json').exists() and not (p/'machine-id-cases-4.json').exists()
old=[json.loads(s) for s in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()];assert len(old)==18
failed=[r for r in old if r['result']!='OK'];assert len(failed)==4
assert all('daemon did not start in 10 seconds' in r.get('stderr','') for r in failed)
registered=json.loads((p/'compile/meson-info/intro-tests.json').read_text());names={'Tests.test_language','Tests.test_languages','Tests.test_startup','Tests.test_user_properties'}
selected=[r for r in registered if r['name'] in names];assert len(selected)==4
assert not (p/'initial-testlog-2.json').exists();(p/'initial-testlog-2.json').write_bytes((p/'compile/meson-logs/testlog.json').read_bytes())
before=json.loads((p/'original-elfs-before-diagnosis-3.json').read_text())
for name,sha in before.items():assert hashlib.sha256((p/'compile'/name).read_bytes()).hexdigest()==sha
worker=r'''import json,os,runpy,sys,unittest
from pathlib import Path
source,case,output=sys.argv[1:];directory=Path(output);directory.mkdir()
namespace=runpy.run_path(source,run_name='accountsservice_original_case');Tests=namespace['Tests'];stop=Tests.stop_daemon;counter=[0]
def preserve(self):
 if self.log:
  counter[0]+=1;data=Path(self.log.name).read_bytes()
  with (directory/(str(counter[0])+'.log')).open('xb') as f:os.fchmod(f.fileno(),0o600);f.write(data)
 stop(self)
Tests.stop_daemon=preserve
assert case.startswith('Tests.')
result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([Tests(case.split('.',1)[1])]))
raise SystemExit(0 if result.wasSuccessful() else 1)
'''
results=[]
for row in selected:
 env={**os.environ,**row['env'],'PYTHONDONTWRITEBYTECODE':'1'};source='/build/source/accountsservice-26.27.3/tests/test-daemon.py'
 r=subprocess.run(['python3','-c',worker,source,row['name'],str(p/(row['name']+'-logs-4'))],env=env,capture_output=True,text=True,timeout=row['timeout']+15)
 result={'name':row['name'],'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr};results.append(result)
(p/'machine-id-cases-4.json').write_text(json.dumps(results,indent=2)+'\n')
assert all(r['exit']==0 and re.search(r'Ran 1 test',r['stderr']) and '\nOK\n' in r['stderr'] for r in results)
for name,sha in before.items():assert hashlib.sha256((p/'compile'/name).read_bytes()).hexdigest()==sha
with (p/'stage.log').open('x') as log:subprocess.run(['meson','install','-C','/build/compile','--destdir','/stage','--no-rebuild','--skip-subprojects'],stdout=log,stderr=subprocess.STDOUT,check=True)
env={**os.environ,'LD_LIBRARY_PATH':'/stage/usr/lib','GI_TYPELIB_PATH':'/stage/usr/lib/girepository-1.0','PYTHONDONTWRITEBYTECODE':'1'}
with (p/'native-consumer.json').open('x') as log:subprocess.run(['python3','/src/toddy-probe.py','/stage'],env=env,stdout=log,check=True)
proof={'scope':'Original14runtime programs reused plus four original daemon cases with synthetic machine ID and log-only teardown instrumentation; mocklibc/mock bus are fixtures, no real account/privilege/GDM acceptance','compile_exit':0,'stage_exit':0,'source_version':'26.27.3','reused_original_programs':14,'repaired_original_cases':[{k:r[k] for k in ['name','exit']} for r in results],'original_failure_retained':'Daemon aborted missing synthetic /etc/machine-id; no timeout accepted as success','unchanged_original_elfs':before,'consumer':json.loads((p/'native-consumer.json').read_text()),'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
assert not any('mocklibc' in n for n in proof['stage_sha256'])
(p/'stage-results.json').write_text(json.dumps(proof,indent=2)+'\n')
