#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,os,shutil,subprocess,sys,tempfile,shlex,xml.etree.ElementTree as ET
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','modemmanager'],text=True)=='install ok installed 1.24.2-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2');from qualify_modemmanager import qualify,digest
proof=qualify(Path('/opt/toddy-build'))
for relative,sha in proof['stage_sha256'].items():assert digest(T/relative)==sha
policy=T/'usr/share/polkit-1/actions/org.freedesktop.ModemManager1.policy'
tree=ET.parse(policy);actions=tree.findall('action');assert actions
defaults=[(a.attrib['id'],{x.tag:x.text for x in a.find('defaults')}) for a in actions]
assert all(d.get('allow_any','no')=='no' and d['allow_inactive']=='no' for _,d in defaults)
assert all(d['allow_active'] in ('auth_self_keep','auth_admin_keep','auth_admin') for _,d in defaults)
assert not list((T/'etc/systemd/system').rglob('ModemManager.service')),'No implicit service enablement'
with tempfile.TemporaryDirectory(prefix='toddy-modemmanager-',dir=T/'tmp') as directory:
 p=Path(directory);os.chown(p,101,101);p.chmod(0o755);virtual='/tmp/'+p.name;env['HOME']=virtual
 shutil.copyfile('/opt/toddy-build/scripts/build/phase2/modemmanager-probe.c',p/'probe.c')
 flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs','mm-glib','gio-2.0'],env=env,text=True))
 wrapper='set -euo pipefail; mount --make-rprivate /; mount -t tmpfs -o size=1m,nosuid,nodev tmpfs /mnt/lfs/dev; for name in null zero random urandom; do touch /mnt/lfs/dev/$name; mount --bind /dev/$name /mnt/lfs/dev/$name; done; exec chroot --userspec=101:101 /mnt/lfs "$@"'
 command=['unshare','--mount','--pid','--fork','--net','bash','-c',wrapper,'toddy-modemmanager']
 launcher="import ctypes,os,sys; assert os.geteuid()==os.getegid()==101; assert ctypes.CDLL(None,use_errno=True).prctl(38,1,0,0,0)==0; os.execv(sys.argv[1],sys.argv[1:])"
 subprocess.run(command+['python3','-c',launcher,'/usr/bin/cc',virtual+'/probe.c','-o',virtual+'/probe',*flags],env=env,check=True,timeout=30)
 actual=subprocess.check_output(command+['python3','-c',launcher,virtual+'/probe'],env=env,text=True,timeout=15)
 assert actual=='MM local C Unicode properties/reset/two fresh cycles; no credentials/device/service access\n'
 gi="import gi\ngi.require_version('ModemManager','1.0')\nfrom gi.repository import ModemManager as M\nfor cycle in range(2):\n p=M.SimpleConnectProperties.new()\n assert p.get_apn() is None\n p.set_apn('offline.example')\n assert p.get_apn()=='offline.example'\n try:p.set_apn(None)\n except TypeError:pass\n else:raise AssertionError('Nonnullable GIR setter accepted None')\n assert p.get_apn()=='offline.example'\n p=M.SimpleConnectProperties.new()\n assert p.get_apn() is None\nprint('MM GI local properties/None refusal/two fresh recoveries')\n"
 introspection=subprocess.check_output(command+['python3','-c',launcher,'/usr/bin/python3','-c',gi],env=env,text=True,timeout=15);assert introspection.strip()=='MM GI local properties/None refusal/two fresh recoveries'
 version=subprocess.check_output(command+['python3','-c',launcher,'/usr/bin/mmcli','--version'],env=env,text=True,timeout=15);assert version==proof['consumer']['version']
 bad=subprocess.run(command+['python3','-c',launcher,'/usr/bin/mmcli','--list-modems'],env=env,text=True,capture_output=True,timeout=15);assert bad.returncode!=0 and "couldn't get bus" in bad.stderr and 'No such file or directory' in bad.stderr
 for cycle in range(2):assert subprocess.check_output(command+['python3','-c',launcher,'/usr/bin/mmcli','--version'],env=env,text=True,timeout=15)==version
 daemon=subprocess.check_output(command+['python3','-c',launcher,'/usr/sbin/ModemManager','--version'],env=env,text=True,timeout=15);assert '1.24.2' in daemon
libs=subprocess.check_output(prefix+['ldd','/usr/lib/libmm-glib.so.0'],env=env,text=True);assert 'not found' not in libs
assert subprocess.check_output(prefix+['pkg-config','--modversion','mm-glib'],env=env,text=True).strip()=='1.24.2'
s=os.statvfs(T);assert s.f_bavail*s.f_frsize>=16*1024**3
Path('/var/log/toddy/phase2/modemmanager-installed-consumer.json').write_text(json.dumps({'scope':'Owned ModemManager1.24.2 SDK/daemon/plugin/service/policy payload and UID101/NNP/private-device/no-route local C/GI Unicode properties/reset/two fresh cycles, CLI absent-system-bus refusal, daemon version, ABI/APT. Strict static policy checked, service not enabled. No running daemon/session authorization/modem/cellular/firmware/Settings GUI/physical acceptance.','C_consumer':actual,'GI_consumer':introspection,'version':version,'daemon_version':daemon,'installed_stage_files_identical':len(proof['stage_sha256']),'strict_policy_defaults':defaults,'shared_library_resolution':True,'physical_modem_tested':False},indent=2)+'\n')
PY
