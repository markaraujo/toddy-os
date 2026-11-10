"""Classify exact original lexical failures and check unchanged production arithmetic."""
from pathlib import Path
import hashlib,json,os,shlex,subprocess

def hashes(base,elf=False):
 return {str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest() for p in base.rglob('*') if p.is_file() and not p.is_symlink() and (not elf or p.open('rb').read(4)==b'\x7fELF')}
def main(probe):
 w=Path('/build');out=w/'numeric-5';out.mkdir()
 stage=json.loads((w/'stage-results.json').read_text());census=json.loads((w/'sparql-census-4/result.json').read_text())
 assert census['state']=='complete-with-failures' and len(census['results'])==491 and len(census['failures'])==4 and census['all_compiled_and_stage_hashes_unchanged']
 exceptions={
 '/core/sparql/aggregates/aggregate-1':[('3.33333333333333','3.3333333333333335')],
 '/core/sparql/aggregates/aggregate-distinct-1':[('3.33333333333333','3.3333333333333335')],
 '/core/sparql/bind/bind3':[('0.0238095238095238','0.023809523809523808'),('0.0588235294117647','0.058823529411764705')],
 '/core/sparql/update/delete-where-query-3':[('0.444444444444444','0.44444444444444442')]}
 for failure in census['failures']:
  pairs=exceptions[failure['case']];p=w/'sparql-census-4'/failure['log'];assert hashlib.sha256(p.read_bytes()).hexdigest()==failure['log_sha256']
  text=p.read_text();assert failure['exit']==-6 and 'Tracker-FATAL-ERROR: --- /src/tests/core/' in text and 'Bail out!' in text
  for old,new in pairs:assert ('"'+old+'"') in text and ('"'+new+'"') in text and format(float(new),'.15g')==old
 for base,key,elf in [('compile','artifacts',True),('test-compile','test_artifacts',True),('stage','stage_sha256',False)]:assert hashes(w/base,elf)==stage[key]
 (out/'probe.c').write_text(probe)
 flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','gio-2.0'],text=True))
 subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(out/'probe.c'),'-I/stage/usr/include/tinysparql-3.0','-L/stage/usr/lib','-Wl,-rpath,/stage/usr/lib',*flags,'-ltinysparql-3.0','-o',str(out/'probe')],check=True)
 result=json.loads(subprocess.check_output([str(out/'probe')],text=True,timeout=30))
 for base,key,elf in [('compile','artifacts',True),('test-compile','test_artifacts',True),('stage','stage_sha256',False)]:assert hashes(w/base,elf)==stage[key]
 result.update(scope='Exact four original tests remain failed lexical goldens, 487 original cases passed. Production typed arithmetic and lossless text independently verified; original code/goldens/SQLite settings untouched. Not full-suite/functional/desktop acceptance.',original_cases_passed=487,original_lexical_failures_retained=exceptions,all_compiled_and_stage_hashes_unchanged=True)
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
