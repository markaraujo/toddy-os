"""Accept source-bound real native account outcomes without replaying them."""
import fcntl,hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path('/opt/toddy-build');LOG=Path('/var/log/toddy/phase2')
FIXTURE=Path('/mnt/lfs/sources/phase2/native-fixtures/accountsservice-1')
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def validate(data):
 accepted=json.loads((FIXTURE/'accepted.json').read_text());report=data['report'];summary=data['summary']
 assert data['child_stopped'] and data['child_exit']==0 and not data['child_oom'] and data['parent_verified_before_builder_restart']
 assert summary['all_selected_exits_zero'] and summary['report_sha256']==hashlib.sha256(json.dumps(report,sort_keys=True).encode()).hexdigest()
 assert report['kernel']=='7.1.8-toddy' and report['fixture_manifest_sha256']==digest(FIXTURE/'accepted.json') and report['unchanged_fixture_files']==len(accepted['files'])==94
 for name,row in accepted['files'].items():
  p=Path('/mnt/lfs')/name
  if 'sha256' in row:assert not p.is_symlink() and digest(p)==row['sha256']
  else:assert p.is_symlink() and str(p.readlink())==row['symlink']
 runs={r['name']:r for r in report['runs']}
 assert len(runs)==len(report['runs'])==10 and all(r['expected_outcome_passed'] for r in runs.values())
 assert set(runs)=={'real-system-bus-user-lookup','own-real-name-and-actual-passwd-update','other-user-real-name-denied','other-user-password-denied-shadow-unchanged','protected-shadow-icon-read-refused','administrator-password-change-real-PAM-new-password','old-password-after-change-refused','stop-removes-bus-owner','restart-recovery-password-persists','reconnect-new-owner-and-persistent-user-data'}
 assert runs['real-system-bus-user-lookup']['uids']==[12345,12346] and runs['protected-shadow-icon-read-refused']['no_icon_effect']
 for name in ['administrator-password-change-real-PAM-new-password','restart-recovery-password-persists']:
  r=runs[name];assert r['expected_authenticated'] and set(r['pam_result'].values())=={0} and not r['secrets_retained']
 old=runs['old-password-after-change-refused'];assert not old['expected_authenticated'] and old['pam_result']['auth']!=0 and old['pam_result']['start']==old['pam_result']['end']==0 and not old['secrets_retained']
 assert report['daemon_uid']==0 and report['service_has_no_mock_environment'] and report['upstream_service_hardening_used'] and report['ephemeral_accounts_removed'] and not report['secrets_retained']
 return {'fixture_manifest_sha256':digest(FIXTURE/'accepted.json'),'fixture_files':94,'real_native_expected_outcomes':10}
def main():
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
 data=json.load(sys.stdin);summary=validate(data);receipt=LOG/'accountsservice-native-acceptance-1.json';assert not receipt.exists(),'Reconcile existing acceptance, no repeat'
 result={'state':'native-real-accounts-qualified','summary':summary,'proof':data};part=receipt.with_suffix('.part');assert not part.exists()
 with part.open('x') as f:json.dump(result,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 part.replace(receipt);print(json.dumps({'state':result['state'],'summary':summary}))
if __name__=='__main__':main()
