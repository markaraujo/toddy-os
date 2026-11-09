"""Same-version GTK3 cache/legal-only native transaction; no runtime rebuild."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
from package_copyright import write_copyright
from schema_union_install import verify
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from stage_package import payload
R=Path('/opt/toddy-build');T=Path('/mnt/lfs');L=Path('/var/log/toddy/phase2')
OLD='3.24.52-1+toddy1';NEW='3.24.52-1+toddy2';CACHE='/usr/lib/gtk-3.0/3.0.0/immodules.cache'
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 source=T/'sources/phase2/inputs/gtk3-ibus-cache-1';work=T/'sources/phase2/work/gtk3-ibus-cache-1'
 proof=json.loads((source/'toddy-input.json').read_text());r=json.loads((work/'test-results.json').read_text())
 assert (L/'gtk3-ibus-cache-1.exit').read_text().strip()=='1'
 body=(R/'scripts/build/phase2/gtk3_ibus_cache_build.py').read_text()
 prefix=['/bin/bash',str(R/'scripts/build/phase2/isolated.sh'),str(source),str(work)]
 initial=json.loads((L/'gtk3-ibus-cache-1.job.json').read_text())['command']
 assert initial[:len(prefix)+2]==prefix+['python3','-c']
 assert initial[-1].replace("'ibus','/usr/share/locale','ja:ko:zh:*'","'ibus','','ja:ko:zh:*'")==body
 assert (L/'gtk3-ibus-cache-metadata-2.exit').read_text().strip()=='0'
 assert json.loads((L/'gtk3-ibus-cache-metadata-2.job.json').read_text())['command']==prefix+['python3','-c',(R/'scripts/build/phase2/gtk3_ibus_cache_finish.py').read_text(),body]
 assert r['query_exit']==0 and r['old_module_count']==11 and r['new_module_count']==12
 assert r['modules']==proof['modules'] and r['baseline_cache_sha256']==proof['old_cache_sha256']
 assert digest(work/'immodules.cache')==r['cache_sha256']
 assert digest(T/CACHE.lstrip('/'))==proof['old_cache_sha256']
 assert digest(T/proof['tool'].lstrip('/'))==proof['tool_sha256']==r['tool_sha256']
 directory=T/'usr/lib/gtk-3.0/3.0.0/immodules'
 assert {'/'+str(p.relative_to(T)) for p in directory.glob('*.so')}==set(proof['modules'])
 for name,row in proof['modules'].items():
  owner=json.loads(Path('/var/log/toddy/packages',row['owner']+'_'+row['version']+'_amd64.json').read_text());assert owner['installed']
  assert digest(T/name.lstrip('/'))==owner['payload'][name]['sha256']==row['sha256']
 old=json.loads(Path('/var/log/toddy/packages','gtk3_'+OLD+'_amd64.json').read_text());assert old['installed'];verify(old)
 archive=Path('/var/cache/toddy/packages','gtk3_'+OLD+'_amd64.deb');assert digest(archive)==old['archive_sha256']==proof['old_archive_sha256']
 assert subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Version}','gtk3'],text=True)==OLD
 reverse=subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Package} ${Depends}\n'],text=True)
 assert 'gtk3 (= ' not in reverse,'Review exact revision pins before changing GTK3'
 depends=subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Depends}','gtk3'],text=True)
 stage=T/'sources/stage/phase2-gtk3-ibus-cache';receipt=L/'gtk3-ibus-cache-transaction-1.json'
 assert not stage.exists() and not receipt.exists()
 for suffix,base in [('.deb','/var/cache/toddy/packages'),('.json','/var/log/toddy/packages')]:assert not Path(base,'gtk3_'+NEW+'_amd64'+suffix).exists()
 size=sum((T/n.lstrip('/')).stat().st_size for n,row in old['payload'].items() if 'sha256' in row)
 assert shutil.disk_usage(T).free>16*1024**3+2*size+32*1024**2
 data={'state':'prepared','scope':'GTK3 same-upstream cache/legal-only revision; all existing runtime/header/config and prior IM registration payload preserved. No user settings or graphical keyboard proof.','old_version':OLD,'new_version':NEW,'old_archive_sha256':old['archive_sha256'],'old_cache_sha256':proof['old_cache_sha256'],'new_cache_sha256':r['cache_sha256'],'modules':proof['modules'],'recovery':'Inspect actual package/transaction/postconditions before action; retain old GTK3 archive/record/cache and module input hashes. Future module install/removal must regenerate this owned cache through a controlled transaction; general module lifecycle is not qualified here. No rollback/replay executed.'}
 def save():receipt.write_text(json.dumps(data,indent=2)+'\n')
 save();stage.mkdir();subprocess.run(['dpkg-deb','-x',str(archive),str(stage)],check=True);assert payload(stage)==old['payload']
 shutil.copyfile(work/'immodules.cache',stage/CACHE.lstrip('/'));archives=proof['source_archives'];write_copyright(stage,'gtk3',archives)
 updated=payload(stage)
 for name in set(updated)|set(old['payload']):
  if name==CACHE or name.startswith('/usr/share/doc/gtk3/'):continue
  assert updated.get(name)==old['payload'].get(name),name
 data['state']='installing';save()
 subprocess.run([sys.executable,str(R/'scripts/build/stage_package.py'),'gtk3',NEW,str(stage),*[arg for a in archives for arg in ['--source',a]],'--recipe','scripts/build/phase2/gtk3-ibus-cache-install.sh','--depends',depends,'--install'],cwd=R,check=True)
 new=json.loads(Path('/var/log/toddy/packages','gtk3_'+NEW+'_amd64.json').read_text());assert new['installed'];verify(new)
 data.update(state='complete',archive_sha256=new['archive_sha256'],old_nonlegal_entries_unchanged=sum(n!=CACHE and not n.startswith('/usr/share/doc/gtk3/') for n in old['payload']))
 save()
if __name__=='__main__':main()
