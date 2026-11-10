"""Bind full dynamic-user GDM source/stage and real shared PAM prerequisites."""
from pathlib import Path
import hashlib,json,subprocess
from verify_stage import inspect_stage

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 T=Path('/mnt/lfs');s=T/'sources/phase2/inputs/gdm-50.2';w=T/'sources/phase2/work/gdm-1';l=Path('/var/log/toddy/phase2')
 for a,b in [('toddy-build.sh','gdm-build.sh'),('toddy-probe.c','gdm-probe.c')]:assert (s/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
 assert (l/'gdm-1.exit').read_text().strip()=='0'
 assert json.loads((l/'gdm-1.job.json').read_text())['command']==['/bin/bash',str(root/'scripts/build/phase2/isolated.sh'),str(s),str(w),'bash','/src/toddy-build.sh']
 prepared=json.loads((s/'toddy-prepared.json').read_text());assert prepared['private_test_sdk']['upstream_sdk_cases_reused']==9 and inspect_stage(s/'toddy-test-sdk')==prepared['private_test_sdk']['manifest']
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
 assert r['original_tests']==[{'name':'gdm:m-common','result':'OK','returncode':0}]
 assert r['consumer']=={'actual_client_and_owned_extension_copies':True,'precancelled_connection_refused':True,'recovery_cycles':2,'actual_login_PAM_or_desktop_tested':False}
 assert r['daemon_version']=='GDM 50.2' and len(r['artifacts'])==79 and len(r['stage_sha256'])==218
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in r[key].items():assert digest(w/base/name)==sha
 config=(w/'compile/config.h').read_text();assert '#define HAVE_USERDB' in config and '#undef ENABLE_X11_SUPPORT' in config
 assert (T/'usr/lib/libnss_systemd.so.2').is_file()
 nss=(T/'etc/nsswitch.conf').read_text()
 for name in ['passwd','group']:assert 'systemd' in next(s.split(':',1)[1].split() for s in nss.splitlines() if s.startswith(name+':'))
 native=json.loads((l/'login-policy-native-accepted-1.json').read_text());assert native['summary']['all_selected_exits_zero'] and native['native_container_exit']==0 and not native['native_container_OOM']
 assert len(native['report']['runs'])==15 and all(q['exit']==0 for q in native['report']['runs']) and len(native['report']['session_cycles'])==2
 for p,sha in native['installed_artifacts'].items():assert digest(T/p.lstrip('/'))==sha
 assert subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Status} ${Version}','toddy-login-policy'],text=True)=='install ok installed 0.1.0-1+toddy1'
 groups=[s.split(':') for s in (T/'etc/group').read_text().splitlines()];assert not any(q[0]=='gdm' or q[2]=='21' for q in groups),'Inspect existing group; never replay initialization'
 assert not any(q.split(':')[0]=='gdm' for q in (T/'etc/passwd').read_text().splitlines()),'Modern GDM uses dynamic greeter users, no obsolete static account'
 assert not (T/'var/lib/gdm').exists()
 return r
