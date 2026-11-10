#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,os,shutil,subprocess,sys,tempfile,shlex
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','libmbim'],text=True)=='install ok installed 1.34.0-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2');from qualify_libmbim import qualify,digest
proof=qualify(Path('/opt/toddy-build'))
for relative,sha in proof['stage_sha256'].items():assert digest(T/relative)==sha
with tempfile.TemporaryDirectory(prefix='toddy-libmbim-',dir=T/'tmp') as directory:
 p=Path(directory);os.chown(p,101,101);p.chmod(0o755);virtual='/tmp/'+p.name;env['HOME']=virtual
 shutil.copyfile('/opt/toddy-build/scripts/build/phase2/libmbim-probe.c',p/'probe.c')
 flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs','mbim-glib','gio-2.0'],env=env,text=True))
 wrapper='set -euo pipefail; mount --make-rprivate /; mount -t tmpfs -o size=1m,nosuid,nodev tmpfs /mnt/lfs/dev; for name in null zero random urandom; do touch /mnt/lfs/dev/$name; mount --bind /dev/$name /mnt/lfs/dev/$name; done; exec chroot --userspec=101:101 /mnt/lfs "$@"'
 command=['unshare','--mount','--pid','--fork','--net','bash','-c',wrapper,'toddy-libmbim']
 launcher="import ctypes,os,sys; assert os.geteuid()==os.getegid()==101; assert ctypes.CDLL(None,use_errno=True).prctl(38,1,0,0,0)==0; os.execv(sys.argv[1],sys.argv[1:])"
 subprocess.run(command+['python3','-c',launcher,'/usr/bin/cc',virtual+'/probe.c','-o',virtual+'/probe',*flags],env=env,check=True,timeout=30)
 actual=subprocess.check_output(command+['python3','-c',launcher,virtual+'/probe'],env=env,text=True,timeout=15)
 assert actual=='MBIM UUID/message C API/invalid UUID and truncated message refusal/two recoveries; no device access\n'
 gi="import gi;gi.require_version('Mbim','1.0');from gi.repository import Mbim;assert Mbim.Message.__gtype__.name=='MbimMessage';print('Mbim1 GI boxed message type available')"
 introspection=subprocess.check_output(command+['python3','-c',launcher,'/usr/bin/python3','-c',gi],env=env,text=True,timeout=15);assert introspection.strip()=='Mbim1 GI boxed message type available'
 version=subprocess.check_output(command+['python3','-c',launcher,'/usr/bin/mbimcli','--version'],env=env,text=True,timeout=15);assert version==proof['consumer']['version']
 bad=subprocess.run(command+['python3','-c',launcher,'/usr/bin/mbimcli','--toddy-invalid-option'],env=env,text=True,capture_output=True,timeout=15);assert bad.returncode!=0 and 'Unknown option' in bad.stderr
libs=subprocess.check_output(prefix+['ldd','/usr/lib/libmbim-glib.so.4'],env=env,text=True);assert 'not found' not in libs
assert subprocess.check_output(prefix+['pkg-config','--modversion','mbim-glib'],env=env,text=True).strip()=='1.34.0'
s=os.statvfs(T);assert s.f_bavail*s.f_frsize>=16*1024**3
Path('/var/log/toddy/phase2/libmbim-installed-consumer.json').write_text(json.dumps({'scope':'Owned libmbim1.34.0 shared/GI/CLI/proxy payload, UID101/NNP/private-dev/no-route C UUID/message/truncation and invalid UUID refusal/two recoveries/GI type/CLI version-invalid option/APT0. Root-only device defaults preserved. No device/proxy-service/cellular network/Settings GUI/physical acceptance.','C_consumer':actual,'GI_consumer':introspection,'version':version,'installed_stage_files_identical':len(proof['stage_sha256']),'shared_library_resolution':True,'root_only_device_authorization':True,'physical_modem_tested':False},indent=2)+'\n')
PY
