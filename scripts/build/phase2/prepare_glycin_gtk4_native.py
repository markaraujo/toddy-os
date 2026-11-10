"""Copy only verified companion stage into a fresh native test fixture."""
from pathlib import Path
import fcntl,hashlib,json,os,shutil,subprocess

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 assert os.geteuid()==0
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
 l=Path('/var/log/toddy/phase2');assert (l/'glycin-gtk4-1.exit').read_text().strip()=='0'
 job=json.loads((l/'glycin-gtk4-1.job.json').read_text());recipe=Path('/opt/toddy-build/scripts/build/phase2/glycin_gtk4_build.py').read_text();assert job['command'][-1]==recipe+'\nmain()\n'
 w=Path('/mnt/lfs/sources/phase2/work/glycin-gtk4-1');r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==r['GI_symbol_exit']==0 and not r['package_promotable'] and not r['image_conversion_tested']
 assert len(r['artifacts'])==78 and len(r['stage_sha256'])==5
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in r[key].items():assert digest(w/base/name)==sha
 assert 'usr/lib/libglycin-gtk4-2.so.0' in r['stage_sha256'] and not any('libglycin-2.' in n or 'glycin-loaders' in n for n in r['stage_sha256'])
 fixture=Path('/mnt/lfs/sources/phase2/native-fixtures/glycin-gtk4-1');receipt=l/'glycin-gtk4-native-fixture.json'
 assert not fixture.exists() and not receipt.exists(),'Reconcile prior fixture state, never replay'
 free=os.statvfs('/mnt/lfs');assert free.f_bavail*free.f_frsize>=16*1024**3+32*1024**2
 package=json.loads(Path('/var/log/toddy/packages/glycin_2.1.5-1+toddy1_amd64.json').read_text());assert package['installed'] and package['archive_sha256']=='b23e696853191f9123354b6144645a515ef24079fb86db8155e2b60d33ef9372'
 core={n:row['sha256'] for n,row in package['payload'].items() if 'sha256' in row and (n.startswith('/usr/lib/') or n.startswith('/usr/libexec/') or n.startswith('/usr/share/glycin'))}
 for name,sha in core.items():assert digest(Path('/mnt/lfs')/name.lstrip('/'))==sha
 state={'state':'preflight','fixture':str(fixture),'stage_sha256':r['stage_sha256'],'installed_core_sha256':core,'installed_core_archive_sha256':package['archive_sha256'],'recipe_sha256':hashlib.sha256(recipe.encode()).hexdigest(),'scope':'Native-test input only; companion is not installed/qualified; original core/loaders remain unchanged.'}
 receipt.write_text(json.dumps(state,indent=2)+'\n');fixture.mkdir(mode=0o755)
 shutil.copytree(w/'stage',fixture/'stage',symlinks=True)
 for name,sha in r['stage_sha256'].items():assert digest(fixture/'stage'/name)==sha
 (fixture/'fixture.json').write_text(json.dumps(state,indent=2)+'\n')
 state['state']='complete';receipt.write_text(json.dumps(state,indent=2)+'\n');print(json.dumps(state))
if __name__=='__main__':main()
