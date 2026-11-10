#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,os,shutil,subprocess,sys,tempfile,shlex
T=Path('/mnt/lfs');prefix=['chroot',str(T)]
env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1',
     'KRB5_CONFIG':'/dev/null','KRB5CCNAME':'MEMORY:toddy-no-credentials'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','mitkrb'],text=True)=='install ok installed 1.22.2-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip()
subprocess.run(prefix+['apt-get','check'],check=True)
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2')
from qualify_mitkrb import qualify,digest
proof=qualify(Path('/opt/toddy-build'))
for relative,sha in proof['stage_sha256'].items():assert digest(T/relative)==sha
ksu=T/'usr/bin/ksu';assert ksu.stat().st_uid==ksu.stat().st_gid==0 and ksu.stat().st_mode&0o7777==0o755
with tempfile.TemporaryDirectory(prefix='toddy-mitkrb-',dir=T/'tmp') as directory:
 p=Path(directory);os.chown(p,101,101);p.chmod(0o755);virtual='/tmp/'+p.name;env['HOME']=virtual
 shutil.copyfile('/opt/toddy-build/scripts/build/phase2/mitkrb-probe.c',p/'probe.c')
 flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs','krb5'],env=env,text=True))
 wrapper='set -euo pipefail; mount --make-rprivate /; mount -t tmpfs -o size=1m,nosuid,nodev tmpfs /mnt/lfs/dev; for name in null zero random urandom; do touch /mnt/lfs/dev/$name; mount --bind /dev/$name /mnt/lfs/dev/$name; done; mount -t proc -o nosuid,nodev,noexec proc /mnt/lfs/proc; exec chroot --userspec=101:101 /mnt/lfs "$@"'
 command=['unshare','--mount','--pid','--fork','--net','bash','-c',wrapper,'toddy-mitkrb']
 launcher="import ctypes,os,sys; assert os.geteuid()==os.getegid()==101; assert ctypes.CDLL(None,use_errno=True).prctl(38,1,0,0,0)==0; assert 'CapEff:\\t0000000000000000' in open('/proc/self/status').read(); os.execv(sys.argv[1],sys.argv[1:])"
 subprocess.run(command+['python3','-c',launcher,'/usr/bin/cc',virtual+'/probe.c','-o',virtual+'/probe',*flags],env=env,check=True,timeout=30)
 actual=subprocess.check_output(command+['python3','-c',launcher,virtual+'/probe'],env=env,text=True,timeout=15)
 assert actual==proof['consumer']
 versions={}
 for executable,args in [('krb5-config',['--version']),('klist',['-V'])]:
  version=subprocess.check_output(command+['python3','-c',launcher,'/usr/bin/'+executable,*args],env=env,text=True,stderr=subprocess.STDOUT,timeout=10)
  assert '1.22.2' in version;versions[executable]=version.strip()
 refusal=subprocess.run(command+['python3','-c',launcher,'/usr/bin/klist','-c','MEMORY:toddy-absent'],env=env,text=True,capture_output=True,timeout=10)
 assert refusal.returncode==1 and 'No credentials cache found' in refusal.stderr
 recovery=subprocess.check_output(command+['python3','-c',launcher,'/usr/bin/krb5-config','--version'],env=env,text=True,timeout=10)
 assert recovery.strip()==versions['krb5-config']
for relative in proof['stage_sha256']:
 if (T/relative).open('rb').read(4)==b'\x7fELF':
  libraries=subprocess.check_output(prefix+['ldd','/'+relative],env=env,text=True)
  assert 'not found' not in libraries
assert subprocess.check_output(prefix+['pkg-config','--modversion','krb5'],env=env,text=True).strip()=='1.22.2'
s=os.statvfs(T);assert s.f_bavail*s.f_frsize>=16*1024**3
Path('/var/log/toddy/phase2/mitkrb-installed-consumer.json').write_text(json.dumps({
 'scope':'Owned frozen MIT Kerberos1.22.2 with3required source patches. Actual installed UID101/no capabilities/NNP/private-device/no-route local C principal/MEMORY-cache reopen/destroy/realm and absent-principal refusals/two recoveries; CLI version/absent-cache refusal/recovery, exact payload/ksu0755/ABI/PC/APT. No owner credentials, real tickets, realm/network authentication, daemon activation, login integration, Settings GUI or physical acceptance.',
 'C_consumer':actual,'CLI_versions':versions,'CLI_absent_cache_exit':refusal.returncode,
 'CLI_recovery':recovery.strip(),'installed_stage_regular_files':len(proof['stage_sha256']),
 'shared_library_resolution':True,'ksu_mode':'root:root0755, no setuid/setgid',
 'physical_machine_tested':False},indent=2)+'\n')
PY
