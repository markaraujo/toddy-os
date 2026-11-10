#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,os,shutil,subprocess,sys,tempfile,shlex
T=Path('/mnt/lfs');prefix=['chroot',str(T)]
env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','cups'],text=True)=='install ok installed 2.4.19-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip()
subprocess.run(prefix+['apt-get','check'],check=True)
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2')
from qualify_cups import qualify,digest
from cups_native import OWNERS,lookup
proof=qualify(Path('/opt/toddy-build'))
for relative,sha in proof['stage_sha256'].items():assert digest(T/relative)==sha
for relative,(uid,gid,mode) in OWNERS.items():
 s=(T/relative.lstrip('/')).stat();assert (s.st_uid,s.st_gid,s.st_mode&0o7777)==(uid,gid,mode)
user=lookup('passwd','lp');assert user[2:4]==['9','9'] and user[5:]==['/var/spool/cups','/bin/false']
assert lookup('group','lpadmin')[2:]==['19','']
shadow=next(line.split(':') for line in (T/'etc/shadow').read_text().splitlines() if line.startswith('lp:'));assert shadow[1].startswith(('!','*'))
assert (T/'etc/cups/client.conf').read_text()=='ServerName /run/cups/cups.sock\n'
assert not (T/'run/cups/cups.sock').exists()
for p in (T/'etc/systemd/system').rglob('*'):
 if p.is_symlink():assert 'cups' not in p.name,'Print units must not be enabled by SDK installation'
with tempfile.TemporaryDirectory(prefix='toddy-cups-',dir=T/'tmp') as directory:
 p=Path(directory);os.chown(p,101,101);p.chmod(0o755);virtual='/tmp/'+p.name;env['HOME']=virtual
 shutil.copyfile('/opt/toddy-build/scripts/build/phase2/cups-probe.c',p/'probe.c')
 flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs','cups'],env=env,text=True))
 wrapper='set -euo pipefail; mount --make-rprivate /; mount -t tmpfs -o size=1m,nosuid,nodev tmpfs /mnt/lfs/dev; for name in null zero random urandom; do touch /mnt/lfs/dev/$name; mount --bind /dev/$name /mnt/lfs/dev/$name; done; mount -t proc -o nosuid,nodev,noexec proc /mnt/lfs/proc; exec chroot --userspec=101:101 /mnt/lfs "$@"'
 command=['unshare','--mount','--pid','--fork','--net','bash','-c',wrapper,'toddy-cups']
 launcher="import ctypes,os,sys; assert os.geteuid()==os.getegid()==101; assert ctypes.CDLL(None,use_errno=True).prctl(38,1,0,0,0)==0; assert 'CapEff:\\t0000000000000000' in open('/proc/self/status').read(); os.execv(sys.argv[1],sys.argv[1:])"
 subprocess.run(command+['python3','-c',launcher,'/usr/bin/cc',virtual+'/probe.c','-o',virtual+'/probe',*flags],env=env,check=True,timeout=30)
 actual=subprocess.check_output(command+['python3','-c',launcher,virtual+'/probe'],env=env,text=True,timeout=15);assert actual==proof['consumer']
 paths={}
 for flag,expected in [('--version','2.4.19'),('--serverroot','/etc/cups'),('--serverbin','/usr/lib/cups'),('--datadir','/usr/share/cups')]:
  value=subprocess.check_output(command+['python3','-c',launcher,'/usr/bin/cups-config',flag],env=env,text=True,timeout=10).strip();assert value==expected,(flag,value);paths[flag]=value
 denial="from pathlib import Path\ntry:Path('/etc/cups/cups-files.conf').read_bytes()\nexcept PermissionError:print('private CUPS service configuration denied')\nelse:raise AssertionError('Unexpected private configuration access')"
 refusal=subprocess.check_output(command+['python3','-c',launcher,'/usr/bin/python3','-c',denial],env=env,text=True,timeout=10);assert refusal.strip()=='private CUPS service configuration denied'
 recovery=subprocess.check_output(command+['python3','-c',launcher,'/usr/bin/cups-config','--version'],env=env,text=True,timeout=10);assert recovery.strip()=='2.4.19'
for relative in proof['stage_sha256']:
 if (T/relative).open('rb').read(4)==b'\x7fELF':
  libs=subprocess.check_output(prefix+['ldd','/'+relative],env=env,text=True);assert 'not found' not in libs
assert subprocess.check_output(prefix+['pkg-config','--modversion','cups'],env=env,text=True).strip()=='2.4.19'
conffiles=subprocess.check_output(prefix+['dpkg-query','-W','-f=${Conffiles}','cups'],text=True)
for name in ['cups-files.conf','cupsd.conf','snmp.conf','client.conf']:assert '/etc/cups/'+name+' ' in conffiles
s=os.statvfs(T);assert s.f_bavail*s.f_frsize>=16*1024**3
Path('/var/log/toddy/phase2/cups-installed-consumer.json').write_text(json.dumps({
 'scope':'Owned frozen CUPS2.4.19 full component payload and corrected etc/var/run/usr layout. Installed UID101/NNP/caps0/private-device/no-route local IPP Unicode/add/find/delete/refusal/two recoveries, CLI paths/version/private-config denial/recovery, exact stage bytes/service ownership/locked factory identities/conffiles/ABI/PC/APT. No units enabled or daemon/socket activated. No print job/driver/device/remote SNMP/server/network/TLS connection/Settings GUI/physical acceptance.',
 'C_consumer':actual,'CLI':paths,'private_configuration_refusal':refusal.strip(),'CLI_recovery':recovery.strip(),
 'service_user':{'uid':9,'gid':9,'shell':'/bin/false','locked':True},'admin_group':{'gid':19,'members':[]},
 'exact_owned_service_paths':len(OWNERS),'installed_stage_regular_files':len(proof['stage_sha256']),
 'conffiles_preserved':True,'service_units_enabled':False,'shared_library_resolution':True,'physical_machine_tested':False},indent=2)+'\n')
PY
