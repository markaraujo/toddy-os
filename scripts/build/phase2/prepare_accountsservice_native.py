"""Freeze staged service and qualified PAM consumer for one real native account gate."""
import fcntl,hashlib,json,os,subprocess
from pathlib import Path
from qualify_accountsservice_stage import qualify
from verify_stage import inspect_stage
ROOT=Path('/opt/toddy-build');LOG=Path('/var/log/toddy/phase2')
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
 result=qualify(ROOT);stage=Path('/mnt/lfs/sources/phase2/work/accountsservice-1/stage');manifest=inspect_stage(stage)
 assert Path('/mnt/lfs/var/log/wtmp').is_file() and Path('/mnt/lfs/home').is_dir()
 pam=Path('/mnt/lfs/sources/phase2/native-fixtures/pam-1');client=pam/'password-consumer';accepted_pam=json.loads((pam/'accepted.json').read_text());assert digest(client)==accepted_pam['artifacts']['password-consumer']
 files={}
 for p in stage.rglob('*'):
  if p.is_symlink():files[str(p.relative_to('/mnt/lfs'))]={'symlink':str(p.readlink())}
  elif p.is_file():files[str(p.relative_to('/mnt/lfs'))]={'sha256':digest(p)}
 files[str(client.relative_to('/mnt/lfs'))]={'sha256':digest(client)}
 fixture=Path('/mnt/lfs/sources/phase2/native-fixtures/accountsservice-1');receipt=LOG/'accountsservice-native-prepare-1.json'
 assert not fixture.exists() and not receipt.exists(),'Reconcile prior fixture, never replay'
 fixture.mkdir()
 accepted={'scope':'Real native account/credential/permission/restart gate only; no GDM/graphical acceptance','stage':str(stage.relative_to('/mnt/lfs')),'files':files,'stage_manifest':manifest,'pam_client':str(client.relative_to('/mnt/lfs')),'source_version':'26.27.3','original_fixture_evidence':'14original runtime programs+four corrected original daemon cases, no real account acceptance yet'}
 (fixture/'accepted.json').write_text(json.dumps(accepted,indent=2)+'\n')
 receipt.write_text(json.dumps({'state':'complete','fixture':str(fixture),'manifest_sha256':digest(fixture/'accepted.json'),'artifact_files':len(files)},indent=2)+'\n');print(receipt.read_text())
if __name__=='__main__':main()
