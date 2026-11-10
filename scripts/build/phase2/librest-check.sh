#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,os,shutil,subprocess,sys,tempfile,shlex
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','librest'],text=True)=='install ok installed 0.10.2-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2');from qualify_librest import qualify,digest
proof=qualify(Path('/opt/toddy-build'))
for relative,sha in proof['stage_sha256'].items():assert digest(T/relative)==sha
with tempfile.TemporaryDirectory(prefix='toddy-librest-',dir=T/'tmp') as directory:
 p=Path(directory);os.chown(p,101,101);p.chmod(0o755);virtual='/tmp/'+p.name;env['HOME']=virtual
 shutil.copyfile('/opt/toddy-build/scripts/build/phase2/librest-probe.c',p/'probe.c')
 flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs','rest-1.0'],env=env,text=True))
 wrapper='set -euo pipefail; mount --make-rprivate /; mount -t tmpfs -o size=1m,nosuid,nodev tmpfs /mnt/lfs/dev; for name in null zero random urandom; do touch /mnt/lfs/dev/$name; mount --bind /dev/$name /mnt/lfs/dev/$name; done; exec chroot --userspec=101:101 /mnt/lfs "$@"'
 command=['unshare','--mount','--pid','--fork','--net','bash','-c',wrapper,'toddy-librest']
 launcher="import ctypes,os,sys; assert os.geteuid()==os.getegid()==101; assert ctypes.CDLL(None,use_errno=True).prctl(38,1,0,0,0)==0; os.execv(sys.argv[1],sys.argv[1:])"
 subprocess.run(command+['python3','-c',launcher,'/usr/bin/cc',virtual+'/probe.c','-o',virtual+'/probe',*flags],env=env,check=True,timeout=30)
 actual=subprocess.check_output(command+['python3','-c',launcher,virtual+'/probe'],env=env,text=True,timeout=15)
 assert actual=='UTF8 XML/two malformed refusals/two fresh proxy+parser recoveries; no request sent\n'
 gi="import gi;gi.require_version('Rest','1.0');from gi.repository import Rest;p=Rest.Proxy.new('http://127.0.0.1:1/',False);c=p.new_call();c.set_function('local-only');assert c.get_function()=='local-only';print('Rest1 GI constructor/local call, no request sent')"
 introspection=subprocess.check_output(command+['python3','-c',launcher,'/usr/bin/python3','-c',gi],env=env,text=True,timeout=15)
 assert introspection.strip()=='Rest1 GI constructor/local call, no request sent'
libs=subprocess.check_output(prefix+['ldd','/usr/lib/librest-1.0.so.0'],env=env,text=True);assert 'not found' not in libs
for name in ['libsoup-3.0.so.0','libxml2.so.16']:assert name+' => /usr/lib/'+name in libs
assert subprocess.check_output(prefix+['pkg-config','--modversion','rest-1.0','rest-extras-1.0'],env=env,text=True).splitlines()==['0.10.2','0.10.2']
s=os.statvfs(T);assert s.f_bavail*s.f_frsize>=16*1024**3
Path('/var/log/toddy/phase2/librest-installed-consumer.json').write_text(json.dumps({'scope':'Owned installed librest C/GI UTF8 XML/nonXML refusal/two fresh recoveries/local proxy API only, UID101/NoNewPrivs/private devices/no route. Original local Soup3 tests reused. No actual online-account/provider/login/GUI or blanket XML security acceptance.','C_consumer':actual,'GI_consumer':introspection,'installed_stage_files_identical':len(proof['stage_sha256']),'shared_library_resolution':True,'external_service_cases_unexecuted':proof['unexecuted_external_cases']},indent=2)+'\n')
PY
