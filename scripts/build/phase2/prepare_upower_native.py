"""Freeze completed portable UPower results and unchanged artifacts for real boot."""
import fcntl,hashlib,json,subprocess
from pathlib import Path
ROOT=Path('/opt/toddy-build');LOG=Path('/var/log/toddy/phase2')
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify():
 work=Path('/mnt/lfs/sources/phase2/work/upower-1');source=Path('/mnt/lfs/sources/phase2/inputs/upower-v1.91.3')
 assert (LOG/'upower-1.exit').read_text().strip()=='1' and (LOG/'upower-consumer-4.exit').read_text().strip()=='0'
 assert digest(source/'toddy-build.sh')=='08f5cbb52dfda2ff95b02aa666d9f84974d701d9c6869577bdf02850e61bc681'
 assert digest(source/'toddy-probe.py')=='9b91cc4299c9a7bbc36a37be413bb842ba14a2b4ad9af316f843c1613bc66876'
 job=json.loads((LOG/'upower-consumer-4.job.json').read_text());assert job['command'][2:]==[str(source),str(work),'python3','-c',(ROOT/'scripts/build/phase2/upower_finish.py').read_text(),(ROOT/'scripts/build/phase2/upower-probe.py').read_text()]
 result=json.loads((work/'stage-results.json').read_text());assert result['compile_exit']==result['stage_exit']==0
 assert len(result['original_portable_cases'])==5 and len(result['excluded_system_bus_cases'])==2
 assert result['consumer']['cli_help_exit']==0 and result['consumer']['typed_history_roundtrip'] and result['consumer']['unknown_kind_refused_to_unknown']
 for base,key in [('compile','unchanged_original_elfs'),('stage','stage_sha256')]:
  for name,sha in result[key].items():assert digest(work/base/name)==sha
 return work,source,result
def main():
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
 work,source,result=qualify();fixture=Path('/mnt/lfs/sources/phase2/native-fixtures/upower-1');receipt=LOG/'upower-native-prepare-1.json'
 assert not fixture.exists() and not receipt.exists(),'Reconcile existing native fixture; no replay'
 files={}
 for p in list((work/'stage').rglob('*'))+[work/'compile/src/up_self_test',source/'etc/UPower.conf']:
  if p.is_symlink():files[str(p.relative_to('/mnt/lfs'))]={'symlink':str(p.readlink())}
  elif p.is_file():files[str(p.relative_to('/mnt/lfs'))]={'sha256':digest(p)}
 fixture.mkdir();accepted={'stage':str((work/'stage').relative_to('/mnt/lfs')),'files':files,'original_client':str((work/'compile/src/up_self_test').relative_to('/mnt/lfs')),'original_config':str((source/'etc/UPower.conf').relative_to('/mnt/lfs'))}
 (fixture/'accepted.json').write_text(json.dumps(accepted,indent=2)+'\n')
 receipt.write_text(json.dumps({'state':'complete','fixture':str(fixture),'manifest_sha256':digest(fixture/'accepted.json'),'artifact_files':len(files)},indent=2)+'\n');print(receipt.read_text())
if __name__=='__main__':main()
