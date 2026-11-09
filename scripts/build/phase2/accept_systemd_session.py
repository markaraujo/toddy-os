"""Reconcile real native session results without any package/test replay."""
import fcntl,hashlib,json,os,subprocess
from pathlib import Path
LOG=Path('/var/log/toddy/phase2')
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    run=json.loads(Path('/var/log/toddy/build/b02-systemd-pam-install.success.json').read_text());assert run['recipe_exit']==run['postcheck_exit']==0
    raw=LOG/'native-systemd-session-1-report.json';assert digest(raw)=='f880d12c0f5e4a020e659c1d72b3535290e96f98f82583ed43668b244a8d424f'
    r=json.loads(raw.read_text());assert r['kernel']=='7.1.8-toddy' and r['ephemeral_account_removed'] and not r['passwords_or_tokens_used']
    assert len(r['runs'])==4 and all(x['exit']==0 for x in r['runs'])
    assert r['runs'][0]['name']=='cold-boot-new-PID1-PAM' and '+PAM' in r['runs'][0]['features']
    assert r['runs'][1]['service_cgroup_empty'] and r['runs'][2]['actual_exec_status']==224 and r['runs'][3]['actual_uid']==12345
    assert len(r['session_cycles'])==2
    for x in r['session_cycles']:
        assert x['pam_open_exit']==x['pam_close_exit']==x['pam_end_exit']==x['user_bus_get_id_exit']==0
        assert x['session']['User']=='12345' and x['session']['Type']=='tty' and x['session']['Class']=='user'
        assert x['runtime_owner_uid']==12345 and x['runtime_mode']=='0700'
        assert x['user_manager']==x['user_default_target']=='active' and x['session_and_runtime_removed']
    assert r['session_cycles'][0]['bus_id_sha256']!=r['session_cycles'][1]['bus_id_sha256']
    fixture=Path('/mnt/lfs/sources/phase2/native-fixtures/systemd-session-1');assert digest(fixture/'accepted.json')==r['fixture_manifest_sha256']
    accepted=json.loads((fixture/'accepted.json').read_text());assert len(accepted['artifacts'])==r['unchanged_fixture_files']==1 and len(accepted['installed_artifacts'])==r['unchanged_installed_artifacts']==8
    assert accepted['installed_artifacts']['/usr/lib/systemd/systemd']==r['runs'][0]['pid1_sha256']
    for p,sha in accepted['artifacts'].items():assert digest(fixture/p)==sha
    for p,sha in accepted['installed_artifacts'].items():assert digest(Path('/mnt/lfs')/p.lstrip('/'))==sha
    assert subprocess.check_output(['chroot','/mnt/lfs','dpkg-query','-W','-f=${Status} ${Version}','systemd'],text=True)=='install ok installed 261.2-1+toddy3'
    receipt=LOG/'systemd-session-acceptance-1.json';assert not receipt.exists(),'Read existing acceptance before any repeat'
    proof={'state':'native-boot-session-qualified','version':'261.2-1+toddy3','native_kernel':r['kernel'],'native_report_sha256':digest(raw),'real_policy_cases':4,'real_session_cycles':2,'unchanged_installed_artifacts':8,'scope':'Actual native new PID1/PAMName/Stop/logind/user-manager/user-D-Bus/recovery; no GDM/GNOME or physical acceptance','no_package_or_test_replay':True}
    with receipt.open('x') as f:json.dump(proof,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    print(json.dumps(proof))
if __name__=='__main__':main()
