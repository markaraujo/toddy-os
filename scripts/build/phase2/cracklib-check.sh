#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,os,subprocess,sys,tempfile
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','cracklib'],text=True)=='install ok installed 2.10.3-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2');from qualify_cracklib import qualify,digest
proof=qualify(Path('/opt/toddy-build'))
for relative,sha in proof['stage_sha256'].items():assert digest(T/relative)==sha
with tempfile.TemporaryDirectory(prefix='toddy-cracklib-',dir=T/'tmp') as directory:
 p=Path(directory);os.chown(p,101,101);p.chmod(0o755);virtual='/tmp/'+p.name;env['HOME']=virtual
 wrapper='set -euo pipefail; mount --make-rprivate /; mount -t tmpfs -o size=1m,nosuid,nodev tmpfs /mnt/lfs/dev; for name in null zero random urandom; do touch /mnt/lfs/dev/$name; mount --bind /dev/$name /mnt/lfs/dev/$name; done; exec chroot --userspec=101:101 /mnt/lfs "$@"'
 command=['unshare','--mount','--pid','--fork','--net','bash','-c',wrapper,'toddy-cracklib']
 code="""import ctypes,os,json,hashlib,subprocess
 assert os.geteuid()==os.getegid()==101 and ctypes.CDLL(None,use_errno=True).prctl(38,1,0,0,0)==0
 lib=ctypes.CDLL('/usr/lib/libcrack.so.2');lib.FascistCheck.argtypes=[ctypes.c_char_p,ctypes.c_char_p];lib.FascistCheck.restype=ctypes.c_char_p;lib.GetDefaultCracklibDict.restype=ctypes.c_char_p
 assert lib.GetDefaultCracklibDict()==b'/usr/lib/cracklib/pw_dict'
 fixture=hashlib.sha256(b'public synthetic Cracklib test fixture; never an owner password').hexdigest().encode()
 for i in range(2):
  assert lib.FascistCheck(b'password',None) is not None
  assert lib.FascistCheck(fixture,b'/missing-toddy-test-dictionary')==b'error loading dictionary'
  assert lib.FascistCheck(fixture,None) is None
 r=subprocess.run(['/usr/sbin/cracklib-check','--no-echo'],input=fixture+b'\\n',capture_output=True,check=True);assert r.stdout==b'It is OK\\n'
 print(json.dumps({'C_API':True,'dictionary_default':True,'weak_fixture_refused':True,'missing_dictionary_refused':True,'fresh_recovery_cycles':2,'CLI_no_echo':True,'owner_password_or_PAM_mutated':False}))
 """
 code='\n'.join(x[1:] if x.startswith(' ') else x for x in code.splitlines())
 actual=json.loads(subprocess.check_output(command+['python3','-c',code],env=env,text=True,timeout=30))
for relative,sha in proof['stage_sha256'].items():assert digest(T/relative)==sha
libs=subprocess.check_output(prefix+['ldd','/usr/lib/libcrack.so.2'],env=env,text=True);assert 'not found' not in libs
s=os.statvfs(T);assert s.f_bavail*s.f_frsize>=16*1024**3
Path('/var/log/toddy/phase2/cracklib-installed-consumer.json').write_text(json.dumps({'scope':'Owned installed Cracklib2.10.3 shared C API/tools/default packed exact recommended dictionary; UID101/NoNewPrivs/private-dev/no-route, synthetic weak/missing-dict refusals/two recoveries/no-echo CLI, all stage bytes unchanged. No owner password/PAM/account mutation or blanket multilingual/security acceptance.','consumer':actual,'installed_stage_files_identical':len(proof['stage_sha256']),'shared_library_resolution':True},indent=2)+'\n')
PY
