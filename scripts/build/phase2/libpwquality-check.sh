#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,os,subprocess,sys,tempfile
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','libpwquality'],text=True)=='install ok installed 1.4.5-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2');from qualify_libpwquality import qualify,digest
proof=qualify(Path('/opt/toddy-build'))
for relative,sha in proof['stage_sha256'].items():assert digest(T/relative)==sha
before=json.loads(Path('/var/log/toddy/phase2/libpwquality-pam-before.json').read_text());current={str(p.relative_to(T)):digest(p) for p in (T/'etc/pam.d').rglob('*') if p.is_file() and not p.is_symlink()};assert current==before
conffiles=subprocess.check_output(prefix+['dpkg-query','-W','-f=${Conffiles}','libpwquality'],text=True);assert '/etc/security/pwquality.conf' in conffiles
with tempfile.TemporaryDirectory(prefix='toddy-pwquality-',dir=T/'tmp') as directory:
 p=Path(directory);os.chown(p,101,101);p.chmod(0o755);virtual='/tmp/'+p.name;env['HOME']=virtual
 wrapper='set -euo pipefail; mount --make-rprivate /; mount -t tmpfs -o size=1m,nosuid,nodev tmpfs /mnt/lfs/dev; for name in null zero random urandom; do touch /mnt/lfs/dev/$name; mount --bind /dev/$name /mnt/lfs/dev/$name; done; exec chroot --userspec=101:101 /mnt/lfs "$@"'
 command=['unshare','--mount','--pid','--fork','--net','bash','-c',wrapper,'toddy-pwquality']
 code="""import ctypes,os,json,hashlib,subprocess
 assert os.geteuid()==os.getegid()==101 and ctypes.CDLL(None,use_errno=True).prctl(38,1,0,0,0)==0
 P=ctypes.c_void_p;S=ctypes.c_char_p;I=ctypes.c_int
 lib=ctypes.CDLL('/usr/lib/libpwquality.so.1')
 for name,args,result in [('pwquality_default_settings',[],P),('pwquality_free_settings',[P],None),('pwquality_set_option',[P,S],I),('pwquality_check',[P,S,S,S,P],I)]:
  f=getattr(lib,name);f.argtypes=args;f.restype=result
 fixture=hashlib.sha256(b'public synthetic pwquality fixture; never an owner password').hexdigest().encode()
 for i in range(2):
  settings=lib.pwquality_default_settings();assert settings
  try:
   assert lib.pwquality_set_option(settings,b'minlen=12')==0
   assert lib.pwquality_check(settings,b'password',None,None,None)<0
   assert lib.pwquality_set_option(settings,b'minlen=invalid')<0
   assert lib.pwquality_check(settings,fixture,None,None,None)>=0
  finally:lib.pwquality_free_settings(settings)
 good=subprocess.run(['/usr/bin/pwscore'],input=fixture+b'\\n',capture_output=True);assert good.returncode==0 and 0<=int(good.stdout)<=100
 weak=subprocess.run(['/usr/bin/pwscore'],input=b'password\\n',capture_output=True);assert weak.returncode!=0
 empty=subprocess.run(['/usr/bin/pwscore'],input=b'',capture_output=True);assert empty.returncode==4
 print(json.dumps({'C_API':True,'weak_fixture_refused':True,'invalid_setting_refused':True,'fresh_recovery_cycles':2,'CLI_positive_weak_and_empty':True,'owner_password_or_PAM_mutated':False}))
 """
 code='\n'.join(x[1:] if x.startswith(' ') else x for x in code.splitlines())
 actual=json.loads(subprocess.check_output(command+['python3','-c',code],env=env,text=True,timeout=30))
libs=subprocess.check_output(prefix+['ldd','/usr/lib/libpwquality.so.1'],env=env,text=True);assert 'libcrack.so.2 => /usr/lib/libcrack.so.2' in libs and 'not found' not in libs
module=subprocess.check_output(prefix+['ldd','/usr/lib/security/pam_pwquality.so'],env=env,text=True);assert 'libpam.so.0 => /usr/lib/libpam.so.0' in module and 'not found' not in module
assert subprocess.check_output(prefix+['pkg-config','--modversion','pwquality'],env=env,text=True).strip()=='1.4.5'
s=os.statvfs(T);assert s.f_bavail*s.f_frsize>=16*1024**3
Path('/var/log/toddy/phase2/libpwquality-installed-consumer.json').write_text(json.dumps({'scope':'Owned installed libpwquality1.4.5 C API/CLI/SDK and inactive PAM module; UID101/NNP/private-dev/no-route, synthetic weak/invalid-setting/empty-input refusals/two recoveries/shared ABI/APT/conffile ownership. Active PAM tree unchanged, no owner password/account authentication/GUI/general-security acceptance.','consumer':actual,'installed_stage_files_identical':len(proof['stage_sha256']),'shared_library_resolution':True,'active_PAM_files_unchanged':len(before),'PAM_module_authentication_tested':False},indent=2)+'\n')
PY
