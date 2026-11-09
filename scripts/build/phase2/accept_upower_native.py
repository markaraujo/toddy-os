"""Verify original native bus tests and real hardened UPower service evidence."""
import fcntl,hashlib,json,os,re,subprocess,sys
from pathlib import Path
LOG=Path('/var/log/toddy/phase2');FIXTURE=Path('/mnt/lfs/sources/phase2/native-fixtures/upower-1')
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def validate(data):
 accepted=json.loads((FIXTURE/'accepted.json').read_text());report=data['report'];summary=data['summary']
 assert data['child_stopped'] and data['child_exit']==0 and not data['child_oom'] and data['parent_verified_before_builder_restart']
 assert summary['all_selected_exits_zero'] and summary['report_sha256']==hashlib.sha256(json.dumps(report,sort_keys=True).encode()).hexdigest()
 assert report['kernel']=='7.1.8-toddy' and report['fixture_manifest_sha256']==digest(FIXTURE/'accepted.json') and report['unchanged_fixture_files']==len(accepted['files'])==39
 for name,row in accepted['files'].items():
  p=Path('/mnt/lfs')/name
  if 'sha256' in row:assert not p.is_symlink() and digest(p)==row['sha256']
  else:assert p.is_symlink() and str(p.readlink())==row['symlink']
 runs={r['name']:r for r in report['runs']};assert len(runs)==len(report['runs'])==6 and all(r['exit']==0 for r in runs.values())
 assert set(runs)=={'original-system-bus-polkit','original-system-bus-daemon','real-linux-service-query-and-cli-version','invalid-method-refused-state-preserved','stop-removes-bus-owner','restart-reconnect-distinct-owner'}
 for name in ['polkit','daemon']:
  r=runs['original-system-bus-'+name];assert not re.search('skip|not ok',r['stdout']+'\n'+r['stderr'],re.I)
  assert len(re.findall(r'^ok \d+ /power/'+name+'$',r['stdout'],re.M))==1
 assert report['service_has_no_mock_environment'] and report['upstream_service_hardening_used']
 return {'fixture_manifest_sha256':digest(FIXTURE/'accepted.json'),'fixture_files':39,'native_outcomes':6,'original_system_bus_cases':2}
def main():
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
 data=json.load(sys.stdin);summary=validate(data);receipt=LOG/'upower-native-acceptance-1.json';assert not receipt.exists(),'Reconcile prior acceptance; no repeat'
 part=receipt.with_suffix('.part');assert not part.exists()
 with part.open('x') as f:json.dump({'state':'native-linux-service-qualified','summary':summary,'proof':data},f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 part.replace(receipt);print(json.dumps(summary))
if __name__=='__main__':main()
