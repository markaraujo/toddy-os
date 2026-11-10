"""Correct omitted generated-resource metadata; never reinstall or rewrite Info."""
from pathlib import Path
import fcntl,hashlib,json,os,subprocess

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 assert os.geteuid()==0
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 f=open('/var/log/toddy/build/build.lock','a');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
 l=Path('/var/log/toddy/phase2');receipt=l/'aspell-info-metadata-1.json';backup=l/'aspell-package-before-info-metadata-1.json'
 assert not receipt.exists() and not backup.exists(),'Inspect actual metadata/receipt before uncertain replay'
 p=Path('/var/log/toddy/packages/aspell_0.60.8.2-1+toddy1_amd64.json');old=p.read_bytes();r=json.loads(old)
 assert r['installed'] and r['generated_paths']==[] and 'metadata_reconciliation' not in r
 assert r['archive_sha256']=='70368e76eaba8efe0c1195b7f23952eac5c5e49587ad1f9bc3df1df2e3735241'
 assert digest(Path('/var/cache/toddy/packages/aspell_0.60.8.2-1+toddy1_amd64.deb'))==r['archive_sha256']
 assert digest(Path('/opt/toddy-build/scripts/build/stage_package.py'))==r['packager_sha256'],'Bind original producer before future metadata code is synced'
 verify=json.loads(Path('/var/log/toddy/build/b02-aspell-verify-2.success.json').read_text());assert verify['recipe_exit']==verify['postcheck_exit']==verify['changed_paths']==0
 manifest=Path('/var/log/toddy/build/b02-aspell-install.manifest.json');delta=json.loads(manifest.read_text())['/usr/share/info/dir']
 assert '/usr/share/info/dir' not in r['payload'] and digest(Path('/mnt/lfs/usr/share/info/dir'))==delta['after']['sha256']
 docs=sorted(k for k in r['payload'] if k in ['/usr/share/info/aspell.info','/usr/share/info/aspell-dev.info']);assert len(docs)==2
 correction={'scope':'Record existing producer install-info side effect omitted from generated_paths when no prebuilt index staged. No payload/archive/installed index change or native transaction replay.','original_record_sha256':hashlib.sha256(old).hexdigest(),'original_generated_paths':[],'native_change_manifest_sha256':digest(manifest),'index_before_after':delta,'registered_documents':docs}
 state={'state':'intended','package':str(p),'correction':correction};receipt.write_text(json.dumps(state,indent=2)+'\n')
 with backup.open('xb') as output:output.write(old);output.flush();os.fsync(output.fileno())
 r['generated_paths']=['/usr/share/info/dir'];r['metadata_reconciliation']=correction
 part=p.with_suffix('.json.part');assert not part.exists()
 with part.open('x') as output:json.dump(r,output,indent=2);output.write('\n');output.flush();os.fsync(output.fileno())
 part.replace(p)
 assert digest(Path('/mnt/lfs/usr/share/info/dir'))==delta['after']['sha256']
 state.update(state='complete',corrected_record_sha256=digest(p),archive_sha256=r['archive_sha256'],installed_payload_unchanged=True)
 receipt.write_text(json.dumps(state,indent=2)+'\n');print(json.dumps(state))
if __name__=='__main__':main()
