"""Qualify existing Git outputs using its actual aggregate-and-cleanup contract."""
from pathlib import Path
import hashlib,json,os,re,subprocess
assert os.getuid()==101
w=Path('/build');stage=Path('/stage');assert not (w/'stage-results.json').exists()
for n in ['compile.exit','original-tests.exit','stage.exit']:assert (w/n).read_text().strip()=='0',n
log=(w/'original-tests.log').read_text();assert 'aggregate-results-and-cleanup' in (w/'source/t/Makefile').read_text()
assert '$(MAKE) clean' in (w/'source/t/Makefile').read_text()
keys=['fixed','success','failed','broken','total'];totals={}
for key in keys:
 values=re.findall(r'^'+key+r'\s+(\d+)\s*$',log,re.M);assert len(values)==1,(key,values);totals[key]=int(values[0])
assert totals['failed']==0 and totals['total']>30000 and totals['success']>30000
assert totals['total']>=sum(totals[k] for k in ['success','broken','failed'])
groups=sorted(set(re.findall(r'^\*\*\* (t[0-9]{4}-[^\n]+\.sh) \*\*\*$',log,re.M)));assert len(groups)>500,len(groups)
version=subprocess.run([str(stage/'usr/bin/git'),'--version'],capture_output=True,text=True,timeout=15);assert version.returncode==0 and version.stdout.strip()=='git version 2.55.0'
files={}
for p in stage.rglob('*'):
 if not p.is_symlink():assert not p.stat().st_mode&0o6000,p
 if p.is_file() and not p.is_symlink():
  with p.open('rb') as f:files[str(p.relative_to(stage))]=hashlib.file_digest(f,'sha256').hexdigest()
r={'scope':'Actual pinned isolated Git compiler0/full original top-level make test0/stage0; original aggregate totals retain known broken/missing prerequisites. t/Makefile aggregate-results-and-cleanup deliberately deletes individual count files; immutable full transcript/exit proof retained. No compiler/test/staging replay in qualification recovery. Native installed repo/refusal checks pending.','compile_exit':0,'test_exit':0,'stage_exit':0,'qualification_exit':0,'version':version.stdout.strip(),'original_shell_groups':len(groups),'original_shell_group_names':groups,'original_totals':totals,'skipped_or_missing_prerequisite_cases':totals['total']-sum(totals[k] for k in ['success','broken','failed']),'individual_counts_status':'Automatically removed by upstream aggregate-results-and-cleanup after actual test exit0; not fabricated or rerun','stage_sha256':files,'source_profile':{'NO_RUST':'YesPlease','NO_TCLTK':'YesPlease','GIT_UNZIP':'nonexist','private_network':'loopback only, no external route'},'logs':{n:hashlib.sha256((w/n).read_bytes()).hexdigest() for n in ['original-build.log','original-tests.log','original-stage.log']}}
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ['original_shell_group_names','stage_sha256']}))
