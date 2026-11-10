"""Census the previously aborted original driver, preserving code and goldens."""
from pathlib import Path
import hashlib,json,os,re,subprocess,time

def hashes(base,elf=False):
 return {str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest() for p in base.rglob('*') if p.is_file() and not p.is_symlink() and (not elf or p.open('rb').read(4)==b'\x7fELF')}
def main():
 w=Path('/build');p=w/'sparql-census-4';p.mkdir()
 old=json.loads((w/'stage-results.json').read_text());assert old['original_tests_exit']==1
 assert hashes(w/'compile',True)==old['artifacts'] and hashes(w/'test-compile',True)==old['test_artifacts'] and hashes(w/'stage')==old['stage_sha256']
 registered=json.loads((w/'original-registered-tests.json').read_text());matches=[r for r in registered if r['name']=='sparql' and any(s.endswith(':core') or s=='core' for s in r['suite'])];assert len(matches)==1
 row=matches[0];assert row['cmd']==['/build/test-compile/tests/core/tracker-sparql-test'] and not row.get('should_fail',False)
 env=dict(os.environ,**row['env']);env['MALLOC_PERTURB_']='83'
 listed=subprocess.check_output(row['cmd']+['-l'],env=env,text=True,timeout=30);(p/'listed.txt').write_text(listed)
 cases=re.findall(r'^(?:# )?(/core/sparql/[^\r\n]+)$',listed,re.M);assert len(cases)==491 and len(set(cases))==491
 assert re.search(r'^1\.\.491$',listed,re.M), 'Original TAP plan must match selection'
 state={'state':'running','scope':'Actual unmodified debug original driver individual previously unexecuted cases; no source/golden/library rewrite. Initial first-case aggregate fatal failure retained, no rerun of29approved other programs. Census completion is NOT library qualification.','initial_original_failure_retained':True,'planned':len(cases),'results':[],'failures':[],'started_unix':time.time()}
 def save():
  part=p/'result.part';part.write_text(json.dumps(state,indent=2)+'\n');part.replace(p/'result.json')
 save()
 for i,case in enumerate(cases):
  if time.time()-state['started_unix']>600:state['state']='bounded-partial';save();raise SystemExit(1)
  private=Path('/tmp')/('sparql-census-'+str(i));private.mkdir(mode=0o700);childenv=dict(env,TMPDIR=str(private));began=time.monotonic();log=p/('%03d.log'%i)
  try:
   with log.open('xb') as out:r=subprocess.run(row['cmd']+['-p',case],env=childenv,stdout=out,stderr=subprocess.STDOUT,timeout=row['timeout'])
  except subprocess.TimeoutExpired:
   state['state']='timeout-partial';state['results'].append({'case':case,'result':'TIMEOUT','seconds':round(time.monotonic()-began,3),'log':log.name});save();raise SystemExit(1)
  text=log.read_text();record={'case':case,'exit':r.returncode,'seconds':round(time.monotonic()-began,3),'log':log.name,'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()};state['results'].append(record)
  if r.returncode:state['failures'].append(record)
  else:assert re.search(r'^1\.\.1$',text,re.M), 'Single-case selection must not hide extra cases'
  save()
  if (i+1)%50==0:print(json.dumps({'completed':i+1,'failed':len(state['failures'])}),flush=True)
 assert hashes(w/'compile',True)==old['artifacts'] and hashes(w/'test-compile',True)==old['test_artifacts'] and hashes(w/'stage')==old['stage_sha256']
 state.update(state='complete-with-failures' if state['failures'] else 'complete',all_original_cases_passed=not state['failures'],all_compiled_and_stage_hashes_unchanged=True,finished_unix=time.time());save();print(json.dumps({'state':state['state'],'completed':len(state['results']),'failed':len(state['failures'])}),flush=True)
