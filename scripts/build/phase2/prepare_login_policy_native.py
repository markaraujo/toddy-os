"""Reuse qualified clients plus one new token-change client for a fresh native boot."""
from pathlib import Path
import fcntl,hashlib,json,os,shutil,subprocess
R=Path('/opt/toddy-build');T=Path('/mnt/lfs');L=Path('/var/log/toddy/phase2')
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
 receipt=L/'login-policy-native-prepare-1.json';fixture=T/'sources/phase2/native-fixtures/login-policy-1'
 assert not receipt.exists() and not fixture.exists(),'Inspect native fixture state before replay'
 step=json.loads(Path('/var/log/toddy/build/b02-login-policy-install-2.success.json').read_text());assert step['recipe_exit']==step['postcheck_exit']==0
 install=json.loads((L/'login-policy-install-1.json').read_text());assert install['state']=='complete'
 work=T/'sources/phase2/work/login-policy-probe-1';source=T/'sources/phase2/inputs/login-policy-probe-1'
 assert (L/'login-policy-probe-1.exit').read_text().strip()=='0'
 for n in ['login-password-change.c','login-policy-probe-build.sh']:assert (source/n).read_bytes()==(R/'scripts/build/phase2'/n).read_bytes()
 compiled=json.loads((work/'compile-results.json').read_text());assert compiled['compile_exit']==0 and compiled['unprivileged_guard_exit']==64
 assert digest(work/'password-change')==compiled['client_sha256'] and digest(source/'login-password-change.c')==compiled['source_sha256']
 password=T/'sources/phase2/work/pam-1/password-consumer';prior=json.loads((password.parent/'password-client-build.json').read_text());assert digest(password)==prior['client_sha256'] and digest(R/'scripts/build/phase2/pam-password-probe.c')==prior['source_sha256']
 session=T/'sources/phase2/native-fixtures/systemd-session-1/session-consumer';old=json.loads((session.parent/'accepted.json').read_text());assert digest(session)==old['artifacts']['session-consumer']
 policies={n:digest(T/'etc/pam.d'/n) for n in install['input_sha256']};assert policies==install['input_sha256']
 for n,row in install['existing_PAM_policies'].items():assert digest(T/n)==row['sha256']
 names=['/usr/lib/libpam.so.0','/usr/lib/security/pam_unix.so','/usr/lib/security/pam_loginuid.so','/usr/lib/security/pam_systemd.so','/usr/sbin/unix_chkpwd','/usr/lib/systemd/systemd','/usr/lib/systemd/systemd-logind']
 installed={n:digest(T/n.lstrip('/')) for n in names}
 for n in install['input_sha256']:installed['/etc/pam.d/'+n]=policies[n]
 for n,row in install['existing_PAM_policies'].items():installed['/'+n]=row['sha256']
 fixture.mkdir()
 for n,p in [('password-consumer',password),('session-consumer',session),('password-change',work/'password-change')]:shutil.copy2(p,fixture/n)
 for p in [fixture,*fixture.iterdir()]:os.chown(p,0,0)
 accepted={'scope':'Installed four owned PAM includes/native auth/account/password/session qualification; synthetic credentials only in disposable new boot. No GDM/GUI acceptance.','policy_sha256':policies,'existing_PAM_policies':install['existing_PAM_policies'],'installed_artifacts':installed,'artifacts':{p.name:digest(p) for p in fixture.iterdir()},'reused_password_and_session_clients':True,'new_root_client':compiled,'policy_package_archive_sha256':install['archive_sha256']}
 (fixture/'accepted.json').write_text(json.dumps(accepted,indent=2)+'\n')
 receipt.write_text(json.dumps({'state':'complete','fixture':str(fixture),'manifest_sha256':digest(fixture/'accepted.json'),'artifact_files':len(accepted['artifacts']),'installed_artifacts':len(installed)},indent=2)+'\n');print(receipt.read_text())
if __name__=='__main__':main()
