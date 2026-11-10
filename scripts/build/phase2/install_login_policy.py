"""Install only missing owned login policy; preserve all existing PAM policies."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from stage_package import payload
R=Path('/opt/toddy-build');T=Path('/mnt/lfs');L=Path('/var/log/toddy/phase2')
NAMES=['system-auth','system-account','system-password','system-session']
EXPECTED={'system-auth':['auth required pam_unix.so'],'system-account':['account required pam_unix.so'],'system-password':['password required pam_unix.so yescrypt shadow try_first_pass'],'system-session':['session required pam_unix.so','session required pam_loginuid.so','session optional pam_systemd.so']}
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 stage=T/'sources/stage/phase2-toddy-login-policy';receipt=L/'login-policy-install-1.json'
 assert not stage.exists() and not receipt.exists(),'Inspect actual policy transaction; never replay uncertain state'
 assert not Path('/var/cache/toddy/packages/toddy-login-policy_0.1.0-1+toddy1_all.deb').exists()
 existing={str(p.relative_to(T)): {'sha256':digest(p),'mode':p.stat().st_mode,'uid':p.stat().st_uid,'gid':p.stat().st_gid} for p in (T/'etc/pam.d').iterdir() if p.is_file()}
 assert set(p.rsplit('/',1)[-1] for p in existing)=={'other','polkit-auth','systemd-user'},'Review new PAM state before adding policy'
 assert all(not (T/'etc/pam.d'/n).exists() for n in NAMES)
 modules={n:digest(T/'usr/lib/security'/n) for n in ['pam_unix.so','pam_loginuid.so','pam_systemd.so']}
 inputs={}
 for n in NAMES:
  p=R/'config/phase2/pam'/n;lines=[s.strip() for s in p.read_text().splitlines() if s.strip() and not s.startswith('#')];assert lines==EXPECTED[n];inputs[n]=digest(p)
 record={'state':'prepared','scope':'Four additive shared login PAM conffiles only. No existing other/Polkit/systemd-user changes, no nullok/permit, no module/runtime rebuild. Native auth/session tests pending.','existing_PAM_policies':existing,'module_sha256':modules,'input_sha256':inputs,'policy_version':'0.1.0-1+toddy1'}
 def save():
  part=receipt.with_suffix('.part');assert not part.exists();part.write_text(json.dumps(record,indent=2)+'\n');part.replace(receipt)
 save();stage.mkdir();directory=stage/'etc/pam.d';directory.mkdir(parents=True)
 for n in NAMES:
  p=directory/n;p.write_bytes((R/'config/phase2/pam'/n).read_bytes());p.chmod(0o644)
 doc=stage/'usr/share/doc/toddy-login-policy';doc.mkdir(parents=True);(doc/'copyright').write_bytes((R/'LICENSE').read_bytes())
 (doc/'README.Toddy').write_text('Versioned Toddy login PAM includes, based on frozen BLFS13.1 Linux-PAM/Systemd policy. Auth/account use pam_unix; passwords use yescrypt/shadow/try_first_pass; sessions use pam_unix/loginuid/Systemd. No empty-password/permit fallback. Existing deny-only other/Polkit/systemd-user policies remain unchanged. Native module implementations retain their independent licenses. GDM/login/native session qualification is separate.\n')
 for p in [stage,*stage.rglob('*')]:os.chown(p,0,0,follow_symlinks=False)
 record['staged_payload']=payload(stage);record['state']='installing';save()
 subprocess.run([sys.executable,str(R/'scripts/build/stage_package.py'),'toddy-login-policy','0.1.0-1+toddy1',str(stage),'--architecture','all','--recipe','scripts/build/phase2/login-policy-install.sh','--depends','linux-pam (= 1.7.2-1+toddy2), systemd (>= 261.2-1+toddy3)',*[v for n in NAMES for v in ['--conffile','/etc/pam.d/'+n]],'--install'],cwd=R,check=True)
 for name,row in existing.items():
  p=T/name;assert digest(p)==row['sha256'] and (p.stat().st_mode,p.stat().st_uid,p.stat().st_gid)==(row['mode'],row['uid'],row['gid'])
 assert {n:digest(T/'usr/lib/security'/n) for n in modules}==modules
 assert {n:digest(T/'etc/pam.d'/n) for n in NAMES}==inputs
 r=json.loads(Path('/var/log/toddy/packages/toddy-login-policy_0.1.0-1+toddy1_all.json').read_text());assert r['installed'];record.update(state='complete',archive_sha256=r['archive_sha256'],owned_entries=len(r['payload']),existing_PAM_and_modules_unchanged=True);save()
if __name__=='__main__':main()
