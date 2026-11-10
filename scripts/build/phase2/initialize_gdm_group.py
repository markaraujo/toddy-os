"""Finish only the verified installed GDM group, without a package replay."""
from pathlib import Path
import hashlib,json,subprocess,sys
from schema_union_install import verify
T=Path('/mnt/lfs');P=Path('/var/log/toddy/packages/gdm_50.2-1+toddy1_amd64.json')
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 r=json.loads(P.read_text());assert r['installed'] and 'runtime_profile' not in r;verify(r)
 archive=Path('/var/cache/toddy/packages/gdm_50.2-1+toddy1_amd64.deb');assert digest(archive)==r['archive_sha256']
 assert (T/'usr/lib/sysusers.d/gdm.conf').read_text()=='g gdm 21\n'
 groups=[s.split(':') for s in (T/'etc/group').read_text().splitlines()];assert not any(q[0]=='gdm' or q[2]=='21' for q in groups),'Inspect existing group; no uncertain initialization replay'
 assert not any(q.startswith('gdm:') for q in (T/'etc/passwd').read_text().splitlines())
 before={n:digest(T/'etc'/n) for n in ['passwd','shadow']}
 subprocess.run(['chroot',str(T),'groupadd','-g','21','gdm'],check=True)
 group=next(s.split(':') for s in (T/'etc/group').read_text().splitlines() if s.startswith('gdm:'));assert group[2]=='21'
 assert {n:digest(T/'etc'/n) for n in before}==before
 verify(r)
 r['runtime_profile']={'greeter_identity':'GDM50 dynamic userdb users, existing native NSS/Systemd support','dedicated_group':{'name':'gdm','gid':21},'static_gdm_user_created':False,'working_directory':{'path':'/var/lib/gdm','uid':0,'gid':0,'mode':'0755'},'initialization':'Frozen BLFS groupadd only, exact packaged group21 declaration; target has no systemd-sysusers executable. No static user, passwd/shadow or NSS/PAM changes, no daemon activation.','factory_autologin':False,'factory_timed_login':False,'initial_setup_app':'disabled: installer creates owner; optional GNOME initial setup not installed','pending':'Actual dynamic userdb/PAM/keyring/greeter/session/permission/Stop/recovery/native GUI and stock GDM schema cache.'}
 part=P.with_suffix('.part');assert not part.exists();part.write_text(json.dumps(r,indent=2)+'\n');part.replace(P)
 Path('/var/log/toddy/phase2/gdm-group-initialization.json').write_text(json.dumps({'scope':'Finish group-only initialization after verified native package; all payload/archive bytes unchanged, passwd/shadow unchanged, no daemon activation','gid':21,'archive_sha256':r['archive_sha256'],'unchanged_owned_entries':len(r['payload']),'passwd_shadow_unchanged':True},indent=2)+'\n')
if __name__=='__main__':main()
