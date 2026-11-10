"""Reuse successful local CUPS units, qualify resolver, then finish first staging."""
from pathlib import Path
import hashlib,json,os,subprocess,time

def files(base,elf=False):
 return {str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest() for p in base.rglob('*') if p.is_file() and not p.is_symlink() and (not elf or p.open('rb').read(4)==b'\x7fELF')}

def main(recipe, recovery=3):
 assert recovery in (3,4)
 w=Path('/build');receipt=w/('before-finish-'+str(recovery)+'.json');assert not receipt.exists() and not list((w/'stage').iterdir())
 if recovery==4:
  original=json.loads((w/'before-finish-3.json').read_text())
  assert files(w/'tree',True)==original['artifacts']
  assert all(hashlib.sha256((w/n).read_bytes()).hexdigest()==sha for n,sha in original['reused_logs'].items())
  resolver=json.loads((w/'resolver-qualification-1.json').read_text());assert resolver['private_hosts_exact'] and resolver['NoNewPrivs'] and resolver['capabilities']==0
  assert not (w/'original-local-tests.json').exists()
 old=(w/'original-test-build.log').read_text()
 assert old.count('ALL TESTS PASSED!')==2 and 'httpAddrGetList(toddy-builder): FAIL' in old
 assert old.count('1 TESTS FAILED!')==1
 before=files(w/'tree',True);assert before
 logs={n:hashlib.sha256((w/n).read_bytes()).hexdigest() for n in ['original-build.log','original-test-build.log']}
 receipt.write_text(json.dumps({'artifacts':before,'reused_logs':logs},indent=2)+'\n')
 hosts=Path('/etc/hosts');assert hosts.stat().st_uid==0 and hosts.stat().st_mode&0o777==0o644
 assert hosts.read_text()=='127.0.0.1 localhost toddy-builder\n::1 localhost toddy-builder\n'
 env=dict(os.environ,LC_ALL='C',LD_LIBRARY_PATH='/build/tree/cups')
 subprocess.run(['getent','hosts','toddy-builder'],env=env,check=True)
 results=[{'name':n,'exit':0,'reused_original_make_log':True} for n in ['testarray','testfile']]
 for name in ['testi18n','testipp','testhttp','testoptions','testpwg','testraster','testppd','testsnmp']:
  start=time.monotonic()
  with (w/(name+'.log')).open('xb') as log:
   if name in ['testi18n','testipp','testhttp']:command=['./'+name]
   else:command=['make','-C','/build/tree/cups',name]
   result=subprocess.run(command,cwd=w/'tree/cups',env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
   if result.returncode==0 and name=='testsnmp':result=subprocess.run(['./testsnmp'],cwd=w/'tree/cups',env=env,stdout=log,stderr=subprocess.STDOUT,timeout=15)
  results.append({'name':name,'exit':result.returncode,'seconds':round(time.monotonic()-start,3)})
  (w/'original-local-tests.json').write_text(json.dumps(results,indent=2)+'\n');assert result.returncode==0,name
 assert all(files(w/'tree',True)[k]==v for k,v in before.items())
 marker='# Preserve compiled lp/lpadmin policy';assert recipe.count(marker)==1
 subprocess.run(['bash','-euo','pipefail','-c','cd /build/tree\n'+recipe[recipe.index(marker):]],check=True)
 assert all(files(w/'tree',True)[k]==v for k,v in before.items())
 assert all(hashlib.sha256((w/n).read_bytes()).hexdigest()==sha for n,sha in logs.items())
 (w/('finish-'+str(recovery)+'-retained.json')).write_text(json.dumps({'original_ELFs_unchanged':len(before),'original_logs_unchanged':True,'private_hosts_only':True},indent=2)+'\n')
