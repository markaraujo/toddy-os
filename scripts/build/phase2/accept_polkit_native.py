"""Accept actual source-bound native suite/standard-helper proofs, never replay tests."""
import fcntl,hashlib,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path('/opt/toddy-build');LOG=Path('/var/log/toddy/phase2');FIXTURE=Path('/mnt/lfs/sources/phase2/native-fixtures/polkit-suite-1')
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def validate(data):
    accepted=json.loads((FIXTURE/'accepted.json').read_text());manifest=digest(FIXTURE/'accepted.json')
    for name,row in accepted['files'].items():
        p=Path('/mnt/lfs')/name
        if 'sha256' in row:assert not p.is_symlink() and digest(p)==row['sha256']
        else:assert p.is_symlink() and str(p.readlink())==row['symlink']
    for role in ['suite','privilege']:
        item=data[role];report=item['report'];summary=item['summary']
        assert item['child_stopped'] and item['child_exit']==0 and not item['child_oom'] and item['parent_verified_before_builder_restart']
        assert summary['all_selected_exits_zero'] and summary['report_sha256']==hashlib.sha256(json.dumps(report,sort_keys=True).encode()).hexdigest()
        assert report['kernel']=='7.1.8-toddy' and report['fixture_manifest_sha256']==manifest and report['unchanged_fixture_files']==len(accepted['files'])==479
    suite=data['suite']['report'];assert len(suite['runs'])==5 and all(r['exit']==0 and not r['skip_diagnostics'] for r in suite['runs'])
    assert {r['name'] for r in suite['runs']}=={'polkitunixusertest','polkitunixgrouptest','polkitunixnetgrouptest','polkitidentitytest','test-polkitbackendjsauthority'}
    assert sum(len(re.findall(r'^ok \d+',r['stdout'],re.M)) for r in suite['runs'])==59
    report=data['privilege']['report'];runs={r['name']:r for r in report['runs']};assert len(runs)==len(report['runs'])==11
    expected={'allow-kernel-peer':0,'explicit-deny':1,'challenge-without-agent-refused':2,'correct-password-root-execution':0,'unsolicited-cookie-with-correct-password-refused':1,'wrong-password-refused':127,'stop-at-authentication':-2,'recovery-after-stop':0,'no-new-privileges-refuses-setuid-execution':127,'daemon-reconnect-recovery':0,'revoked-policy-replay-refused':1}
    assert {n:r['exit'] for n,r in runs.items()}==expected
    for name in ['correct-password-root-execution','recovery-after-stop']:
        r=runs[name];assert r['expected_authenticated'] and r['pam_prompts']>=1 and r['root_identity_proof']=={'uid':0,'euid':0,'gid':0,'artifact_mode':'0600','parent_mode':'0700'}
    for name in ['correct-password-root-execution','wrong-password-refused','stop-at-authentication','recovery-after-stop']:
        assert not runs[name]['raw_tty_retained'] and runs[name]['active_helper_executables_after_completion']==0
    assert runs['stop-at-authentication']['cancelled_operation_no_effect'] and runs['no-new-privileges-refuses-setuid-execution']['no_new_privileges']
    assert not runs['unsolicited-cookie-with-correct-password-refused']['cookie_retained']
    assert report['distinct_daemon_bus_owners'] and report['ephemeral_account_removed'] and not report['secrets_retained']
    assert report['transport_profile']=='Upstream standard SUID helper fallback; optional systemd helper socket unstarted/unqualified'
    helpers={'/usr/bin/pkexec':'303729b3ce4713fb0ea0554502ea7bb0c87eda38f4f09d501e6dc9f0f70a103a','/usr/lib/polkit-1/polkit-agent-helper-1':'112083c1da8ff12ac29563f97556b7141a36f0981f8b0e450ef504dbc7e0f73b'}
    assert len(report['helpers'])==2 and {r['path']:r['sha256'] for r in report['helpers']}==helpers
    for r in report['helpers']:assert (r['uid'],r['gid'],r['mode'])==(0,0,'4755')
    return {'fixture_manifest_sha256':manifest,'fixture_files':479,'original_programs':5,'observed_original_tap_cases':59,'standard_helper_expected_outcomes':11,'helpers':helpers}
def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    data=json.load(sys.stdin);summary=validate(data);receipt=LOG/'polkit-standard-native-acceptance-1.json'
    assert not receipt.exists(),'Reconcile existing acceptance, no repeat'
    result={'state':'native-standard-helper-qualified','scope':'Verified native original suite plus actual standard SUID helper; optional socket remains unqualified, no parent installation or GNOME UI acceptance','summary':summary,'proofs':data}
    part=receipt.with_suffix('.part');assert not part.exists()
    with part.open('x') as f:json.dump(result,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    part.replace(receipt);print(json.dumps({'state':result['state'],'summary':summary}))
if __name__=='__main__':main()
