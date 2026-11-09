"""Hand off only a source-bound qualified private keygen SDK to Gcr's failed test."""
import fcntl,hashlib,json,os,re,shutil,subprocess,tarfile
from pathlib import Path
ROOT=Path('/opt/toddy-build');LOG=Path('/var/log/toddy/phase2')
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
 sdk=Path('/mnt/lfs/sources/phase2/work/openssh-1');ssh_source=Path('/mnt/lfs/sources/phase2/inputs/openssh-10.5p1');work=Path('/mnt/lfs/sources/phase2/work/gcr-1');source=Path('/mnt/lfs/sources/phase2/inputs/gcr-4.4.0.1')
 assert (LOG/'openssh-keygen-1.exit').read_text().strip()=='1' and (LOG/'openssh-keygen-metadata-2.exit').read_text().strip()=='0'
 assert digest(ssh_source/'toddy-build.sh')=='56ed56d80a19aa537825f425ee12d13bf2e8e228985d674a49c7e691c3ff2f3c'
 assert (ssh_source/'toddy-probe.py').read_bytes()==(ROOT/'scripts/build/phase2/openssh-probe.py').read_bytes()
 assert json.loads((LOG/'openssh-keygen-1.job.json').read_text())['command'][2:]==[str(ssh_source),str(sdk),'bash','/src/toddy-build.sh']
 assert json.loads((LOG/'openssh-keygen-metadata-2.job.json').read_text())['command'][2:]==[str(ssh_source),str(sdk),'python3','-c',(ROOT/'scripts/build/phase2/openssh_keygen_finish.py').read_text()]
 result=json.loads((sdk/'stage-results.json').read_text());assert result['compile_exit']==result['stage_exit']==0 and result['source_version']=='10.5p1'
 for r in result['original_programs']:
  assert r['exit']==0 and digest(sdk/('original-'+r['name']+'.log'))==r['log_sha256']
 assert {r['name']:r['observed_original_cases'] for r in result['original_programs']}=={'sshkey':101,'crypto':18}
 assert result['consumer']['temporary_keys_removed'] and not result['consumer']['key_material_retained'] and result['consumer']['version']=='10.5p1'
 for name,sha in result['unchanged_original_elfs'].items():assert digest(sdk/'compile'/name)==sha
 binary=sdk/'stage/private-test-sdk/bin/ssh-keygen';assert digest(binary)==result['sdk_sha256']==digest(sdk/'compile/ssh-keygen') and binary.stat().st_mode&0o7777==0o755
 assert (LOG/'gcr-1.exit').read_text().strip()=='1'
 assert digest(source/'toddy-build.sh')=='ddf5220f04a57f3f0abca182bda4519154c7d2bee995e844e854bf4a18153ee5'
 assert digest(source/'toddy-probe.c')=='2889245765d3dad60c1d6826f4cf440e800d3f1ec5119a2c42a344d611ef7ef9'
 rows=[json.loads(s) for s in (work/'initial-testlog-1.json').read_text().splitlines() if s.strip()]
 assert len(rows)==39 and sum(r['result']=='OK' and r['returncode']==0 for r in rows)==38
 failed=[r for r in rows if r['result']!='OK'];assert len(failed)==1 and failed[0]['name']=='gcr - gcr:ssh-askpass' and failed[0]['returncode']==-6
 assert 'test-ssh-askpass.c:81:test_ssh_keygen' in failed[0]['stderr']
 sample=source/'gcr/fixtures/pem-rsa-enc.key';assert digest(sample)=='55b32dbd31618e5e949be919fb42ed7ca519f8e4ad5b352c9136ab7202e6ef4e' and sample.stat().st_mode&0o7777==0o644
 destination=work/'test-sdk';receipt=LOG/'gcr-askpass-prepare-1.json';assert not destination.exists() and not receipt.exists(),'Reconcile existing handoff; no replay'
 artifacts={str(p.relative_to(work/'compile')):digest(p) for p in (work/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'};assert artifacts
 record={'state':'prepared','scope':'Private keygen SDK and byte-identical public sample overlay only; original source/assertions/compiled Gcr unchanged, no real credential/GNOME UI claim','sdk_sha256':result['sdk_sha256'],'source_sample_sha256':digest(sample),'source_sample_mode':0o644,'gcr_original_elfs':artifacts,'reused_original_programs':38}
 receipt.write_text(json.dumps(record,indent=2)+'\n');(destination/'bin').mkdir(parents=True);shutil.copyfile(binary,destination/'bin/ssh-keygen');(destination/'bin/ssh-keygen').chmod(0o755)
 assert digest(destination/'bin/ssh-keygen')==result['sdk_sha256'];record['state']='complete';receipt.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:record[k] for k in ['state','sdk_sha256','source_sample_sha256','reused_original_programs']}))
if __name__=='__main__':main()
