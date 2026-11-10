#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,os,subprocess,sys,tempfile
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','gnome-online-accounts'],text=True)=='install ok installed 3.58.1-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2');from qualify_goa import qualify,digest
proof=qualify(Path('/opt/toddy-build'))
for relative,sha in proof['stage_sha256'].items():assert digest(T/relative)==sha
with tempfile.TemporaryDirectory(prefix='toddy-goa-',dir=T/'tmp') as directory:
 p=Path(directory);os.chown(p,101,101);p.chmod(0o755);virtual='/tmp/'+p.name;env.update(HOME=virtual,XDG_CONFIG_HOME=virtual+'/config',XDG_DATA_HOME=virtual+'/data',XDG_CACHE_HOME=virtual+'/cache')
 wrapper='set -euo pipefail; mount --make-rprivate /; mount -t tmpfs -o size=1m,nosuid,nodev tmpfs /mnt/lfs/dev; for name in null zero random urandom; do touch /mnt/lfs/dev/$name; mount --bind /dev/$name /mnt/lfs/dev/$name; done; exec chroot --userspec=101:101 /mnt/lfs "$@"'
 command=['unshare','--mount','--pid','--fork','--net','bash','-c',wrapper,'toddy-goa']
 launcher="import ctypes,os,sys; assert os.geteuid()==os.getegid()==101; assert ctypes.CDLL(None,use_errno=True).prctl(38,1,0,0,0)==0; os.execv(sys.argv[1],sys.argv[1:])"
 version=subprocess.check_output(command+['python3','-c',launcher,'/usr/libexec/goa-daemon','--version'],env=env,text=True,timeout=15);assert version==proof['consumer']['version']
 bad=subprocess.run(command+['python3','-c',launcher,'/usr/libexec/goa-daemon','--toddy-invalid-option'],env=env,capture_output=True,text=True,timeout=15);assert bad.returncode!=0 and 'Unknown option' in bad.stderr
 code="""import gi,json
 gi.require_version('Goa','1.0')
 from gi.repository import Goa
 for i in range(2):
  a=Goa.AccountSkeleton.new();a.props.identity='local-test';a.props.presentation_identity='Olá Toddy 🐾';assert a.props.identity=='local-test' and a.props.presentation_identity=='Olá Toddy 🐾';a.props.identity='';a.props.presentation_identity='';assert a.props.identity==a.props.presentation_identity==''
 print(json.dumps({'namespace':'Goa1','UTF8_account_skeleton':True,'reset_cycles':2,'session_service_tested':False,'real_account_or_secret_created':False}))
 """
 code='\n'.join(x[1:] if x.startswith(' ') else x for x in code.splitlines())
 actual=json.loads(subprocess.check_output(command+['python3','-c',launcher,'/usr/bin/python3','-c',code],env=env,text=True,timeout=15));assert actual['reset_cycles']==2 and not actual['real_account_or_secret_created']
 assert not (p/'config').exists() and not (p/'data').exists()
libs=subprocess.check_output(prefix+['ldd','/usr/lib/libgoa-backend-1.0.so.2'],env=env,text=True);assert 'not found' not in libs
for name in ['libgoa-1.0.so.0','librest-1.0.so.0','libgtk-4.so.1']:assert name+' => /usr/lib/'+name in libs
assert subprocess.check_output(prefix+['pkg-config','--modversion','goa-1.0','goa-backend-1.0'],env=env,text=True).splitlines()==['3.58.1','3.58.1']
service=T/'usr/share/dbus-1/services/org.gnome.OnlineAccounts.service';assert 'Exec=/usr/libexec/goa-daemon' in service.read_text()
s=os.statvfs(T);assert s.f_bavail*s.f_frsize>=16*1024**3
Path('/var/log/toddy/phase2/gnome-online-accounts-installed-consumer.json').write_text(json.dumps({'scope':'Owned GOA3.58.1 core/backend/GI/Vala package, UID101/NoNewPrivs/private-device/no-route daemon CLI/local GI account skeleton/reset only, no account files/credentials created. Session daemon lifecycle, real accounts, provider callbacks/secret integration and Settings/GUI unqualified.','version':version,'invalid_option_refused':True,'GI_consumer':actual,'installed_stage_files_identical':len(proof['stage_sha256']),'shared_library_resolution':True,'providers_unavailable':proof['providers_unavailable'],'own_OAuth_app_identity_required_before_enablement':True},indent=2)+'\n')
PY
