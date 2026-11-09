"""Supply only required en_IE locale data privately; rerun one original case."""
from pathlib import Path
import hashlib,json,os,re,subprocess
assert os.getuid()==101 and Path('/etc/machine-id').read_text()=='00000000000000000000000000000001\n'
p=Path('/build');assert not (p/'stage-results.json').exists() and not list((p/'stage').iterdir())
old=json.loads((p/'machine-id-cases-4.json').read_text());assert len(old)==4
results=[r for r in old if r['exit']==0];assert len(results)==3
failed,=[r for r in old if r['exit']!=0];assert failed['name']=='Tests.test_languages' and "['C', 'en_GB.UTF-8']" in failed['stderr']
assert Path('/usr/share/i18n/locales/en_IE').is_file()
assert '2.44' in subprocess.check_output(['localedef','--version'],text=True).splitlines()[0]
locale_path=p/'locale-fixture-5';assert not locale_path.exists();locale_path.mkdir(mode=0o700)
with (p/'locale-generation-5.log').open('x') as log:subprocess.run(['localedef','--no-archive','-i','en_IE','-f','UTF-8',str(locale_path/'en_IE.UTF-8')],stdout=log,stderr=subprocess.STDOUT,check=True)
env={**os.environ,'LOCPATH':str(locale_path),'PYTHONDONTWRITEBYTECODE':'1'}
subprocess.run(['python3','-c','import locale;assert locale.setlocale(locale.LC_ALL,"en_IE.UTF-8")=="en_IE.UTF-8"'],env=env,check=True)
registered=json.loads((p/'compile/meson-info/intro-tests.json').read_text());row,=[r for r in registered if r['name']=='Tests.test_languages']
worker="import json,os,runpy,sys,unittest\nfrom pathlib import Path\nsource,case,output=sys.argv[1:];directory=Path(output);directory.mkdir()\nnamespace=runpy.run_path(source,run_name='accountsservice_original_case');Tests=namespace['Tests'];stop=Tests.stop_daemon;counter=[0]\ndef preserve(self):\n if self.log:\n  counter[0]+=1;data=Path(self.log.name).read_bytes()\n  with (directory/(str(counter[0])+'.log')).open('xb') as f:os.fchmod(f.fileno(),0o600);f.write(data)\n stop(self)\nTests.stop_daemon=preserve\nassert case.startswith('Tests.')\nresult=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([Tests(case.split('.',1)[1])]))\nraise SystemExit(0 if result.wasSuccessful() else 1)\n"

env.update(row['env'])
r=subprocess.run(['python3','-c',worker,'/build/source/accountsservice-26.27.3/tests/test-daemon.py',row['name'],str(p/'Tests.test_languages-logs-5')],env=env,capture_output=True,text=True,timeout=row['timeout']+15)
result={'name':row['name'],'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
(p/'locale-case-5.json').write_text(json.dumps(result,indent=2)+'\n')
assert r.returncode==0 and re.search(r'Ran 1 test',r.stderr) and '\nOK\n' in r.stderr
results.append(result)
before=json.loads((p/'original-elfs-before-diagnosis-3.json').read_text())
for name,sha in before.items():assert hashlib.sha256((p/'compile'/name).read_bytes()).hexdigest()==sha
with (p/'stage.log').open('x') as log:subprocess.run(['meson','install','-C','/build/compile','--destdir','/stage','--no-rebuild','--skip-subprojects'],stdout=log,stderr=subprocess.STDOUT,check=True)
env={**os.environ,'LD_LIBRARY_PATH':'/stage/usr/lib','GI_TYPELIB_PATH':'/stage/usr/lib/girepository-1.0','PYTHONDONTWRITEBYTECODE':'1'}
with (p/'native-consumer.json').open('x') as log:subprocess.run(['python3','/src/toddy-probe.py','/stage'],env=env,stdout=log,check=True)
proof={'scope':'Original14runtime programs reused plus four original daemon cases with synthetic machine ID/private locale and log-only teardown instrumentation; mocklibc/mock bus are fixtures, no real account/privilege/GDM acceptance','compile_exit':0,'stage_exit':0,'source_version':'26.27.3','reused_original_programs':14,'repaired_original_cases':[{k:r[k] for k in ['name','exit']} for r in results],'locale_fixture':'Private LOCPATH/en_IE.UTF-8 generated using qualified glibc2.44 localedef; no system locale update','previous_machine_id_cases_reused':3,'locale_case_rerun':1,'original_failure_retained':'Daemon aborted missing synthetic /etc/machine-id; no timeout accepted as success','unchanged_original_elfs':before,'consumer':json.loads((p/'native-consumer.json').read_text()),'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
assert not any('mocklibc' in n for n in proof['stage_sha256'])
(p/'stage-results.json').write_text(json.dumps(proof,indent=2)+'\n')
