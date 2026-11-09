"""Require original native units and real target-kernel shadow/helper evidence."""
import hashlib,json
from pathlib import Path
from verify_stage import inspect_stage

def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root,log):
    work=Path('/mnt/lfs/sources/phase2/work/pam-1');source=Path('/mnt/lfs/sources/phase2/inputs/linux-pam-1.7.2-security-1')
    assert (log/'pam-1.exit').read_text().strip()==(log/'pam-password-client-2.exit').read_text().strip()=='0'
    for a,b in [('toddy-build.sh','pam-build.sh'),('toddy-probe.c','pam-probe.c')]:assert (source/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
    prepared=json.loads((source/'toddy-prepared.json').read_text());patches=json.loads((root/'config/phase2/pam-patches.lock.json').read_text())
    assert prepared['source_sha256']==patches['source_sha256'] and prepared['source_patches']==patches['patches']
    for name,sha in prepared['changed_source_files'].items():assert digest(source/name)==sha
    for patch in patches['patches']:assert digest(root/patch['file'])==patch['sha256']
    stage=json.loads((work/'stage-results.json').read_text());rows=[json.loads(r) for r in (work/'compile/meson-logs/testlog.json').read_text().splitlines() if r.strip()]
    registered=json.loads((work/'compile/meson-info/intro-tests.json').read_text())
    assert stage['build_exit']==stage['stage_exit']==stage['consumer_exit']==0
    assert len(rows)==len(registered)==len(stage['original_tests'])==77 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
    client=json.loads((work/'password-client-build.json').read_text());assert client['compile_exit']==0
    assert client['source_sha256']==digest(root/'scripts/build/phase2/pam-password-probe.c') and client['client_sha256']==digest(work/'password-consumer')
    for p,sha in client['unchanged_original_elfs'].items():assert digest(work/p)==sha
    raw=(log/'native-pam-1-report.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='28e4d9c1f7947a929c0d4d75c58677585c5de670c7c797b0d29f801850d5b5c6'
    report=json.loads(raw);assert report['kernel']=='7.1.8-toddy' and report['pid1']=='systemd' and report['ephemeral_account_removed'] and not report['secrets_retained']
    expected=['correct-yescrypt-via-setuid-helper','incorrect-password-refused','empty-password-refused','unknown-user-refused','helper-no-new-privileges-refused','locked-account-refused','unlock-and-authentication-recovery']
    assert [r['name'] for r in report['runs']]==expected and all(r['exit']==0 and r['uid']==12345 for r in report['runs'])
    assert [r['pam_result']['auth'] for r in report['runs']]==[0,7,7,10,9,7,0]
    fixture=Path('/mnt/lfs/sources/phase2/native-fixtures/pam-1');manifest=fixture/'accepted.json'
    assert digest(manifest)==report['fixture_manifest_sha256'];accepted=json.loads(manifest.read_text())
    for name,sha in accepted['artifacts'].items():assert digest(fixture/name)==sha
    assert len(accepted['artifacts'])==report['unchanged_fixture_files']==157
    assert inspect_stage(work/'stage')==inspect_stage(fixture/'stage')
    helper=report['helper'];assert helper==accepted['privileged_helper'] and (helper['uid'],helper['gid'],helper['mode'])==(0,0,0o4755)
    assert digest(work/'stage/usr/sbin/unix_chkpwd')==helper['sha256']
