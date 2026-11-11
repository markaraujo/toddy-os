"""Read observed native ownership/version/source/legal data for the B02 projection."""
from pathlib import Path
import fcntl,hashlib,json,re,subprocess
R=Path('/opt/toddy-build');T=Path('/mnt/lfs')
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
success=json.loads(Path('/var/log/toddy/build/b02-git-install.success.json').read_text());assert success['recipe_exit']==success['postcheck_exit']==0
profile=json.loads((R/'config/phase2/desktop-runtime-roots.json').read_text())
raw=subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${binary:Package}\t${Version}\t${Architecture}\t${Depends}\n'],text=True)
rows={}
for line in raw.splitlines():
 n,v,a,d=line.split('\t',3);rows[n]={'name':n,'version':v,'architecture':a,'depends':d}
seeds=set(profile['retained_foundation_packages']+profile['desktop_roots']);assert seeds<=rows.keys(),sorted(seeds-rows.keys())
closure=set();parents={};queue=list(sorted(seeds))
while queue:
 n=queue.pop()
 if n in closure:continue
 closure.add(n)
 for group in rows[n]['depends'].split(','):
  if not group.strip():continue
  alternatives=[]
  for term in group.split('|'):
   match=re.fullmatch(r'\s*([a-z0-9][a-z0-9+.-]*)(?::(?:any|native|amd64))?(?:\s*\([^)]*\))?\s*',term);assert match,(n,term)
   alternatives.append(match[1])
  chosen=next((x for x in alternatives if x in rows),None);assert chosen,(n,alternatives)
  parents.setdefault(chosen,set()).add(n);queue.append(chosen)
assert not closure.intersection(profile['excluded_product_roots']),sorted(closure.intersection(profile['excluded_product_roots']))
components=[]
for n in sorted(closure):
 row=rows[n];p=Path('/var/log/toddy/packages')/(n+'_'+row['version']+'_'+row['architecture']+'.json');record=json.loads(p.read_text());assert record['installed']
 copyright='/usr/share/doc/'+n+'/copyright';legal=record['payload'].get(copyright);assert legal and 'sha256' in legal,(n,'missing owned copyright')
 actual=T/copyright.lstrip('/');assert not actual.is_symlink()
 with actual.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==legal['sha256']
 index='/usr/share/doc/'+n+'/source-notices/index.json';notice=record['payload'].get(index)
 if notice:
  with (T/index.lstrip('/')).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==notice['sha256']
 components.append({**row,'retained_foundation':n in profile['retained_foundation_packages'],'explicit_desktop_root':n in profile['desktop_roots'],'required_by':sorted(parents.get(n,[])),'archive_sha256':record['archive_sha256'],'component_record_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'recipe_sha256':record['recipe_sha256'],'sources':[{('public_verification_material_sha256' if k=='key_sha256' else k):v for k,v in source.items()} for source in record['sources']],'copyright':{'path':copyright,'sha256':legal['sha256']},'source_notices_index':{'path':index,'sha256':notice['sha256']} if notice else None})
result={'schema_version':1,'scope':profile['scope'],'observed_integration_package_count':len(rows),'runtime_projection_package_count':len(components),'retained_foundation_package_count':len(profile['retained_foundation_packages']),'profile_sha256':hashlib.sha256((R/'config/phase2/desktop-runtime-roots.json').read_bytes()).hexdigest(),'observed_inventory_sha256':hashlib.sha256(raw.encode()).hexdigest(),'components':components,'unselected_integration_packages':[{**rows[n],'classification':'Not selected by declared B02 roots or native Depends. Review actual dynamic/build use during B12 composition; not removal approval.'} for n in sorted(set(rows)-closure)],'limits':'The integration root is not pruned or repackaged here. Recorded native archive/source hashes reuse previously qualified ownership records; current installed versions and legal documents checked read-only. Final B12/B13 image composition/installation/release audit remains required. No agent/model/credential is necessary for this desktop projection.'}
print(json.dumps(result,indent=2))
