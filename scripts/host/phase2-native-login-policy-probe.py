"""Actual installed shared login PAM policies in a fresh native overlay only."""
from pathlib import Path
import base64,hashlib,json,os,re,secrets,signal,stat,subprocess,time,zlib

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def command(args,**kwargs):return subprocess.run(args,text=True,capture_output=True,timeout=25,**kwargs)
def output(args):
 r=command(args);assert r.returncode==0,'Command failed: '+args[0];return r.stdout.strip()
def wait_for(fn,seconds=20):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  if fn():return
  time.sleep(.05)
 raise AssertionError('Bounded actual native postcondition failed')
def main():
 assert os.geteuid()==0 and os.uname().release=='7.1.8-toddy'
 assert Path('/proc/1/comm').read_text().strip()=='systemd'
 assert output(['systemd-detect-virt','--vm']) in ['kvm','qemu']
 device=output(['findmnt','-n','-o','SOURCE','/']);assert re.fullmatch('/dev/[a-z0-9]+',device)
 parent=output(['lsblk','-ndo','PKNAME',device]);assert re.fullmatch('[a-z0-9]+',parent)
 assert output(['lsblk','-dnro','SERIAL','/dev/'+parent])=='TODDY-BOOT-TEST'
 assert output(['blkid','-s','LABEL','-o','value',device])=='TODDY_LFS'
 assert output(['findmnt','-n','-o','FSTYPE','/'])=='ext4'
 assert output(['ip','-o','link','show']).count('\n')==0 and 'lo:' in output(['ip','-o','link','show'])
 fixture=Path('/sources/phase2/native-fixtures/login-policy-1');accepted=json.loads((fixture/'accepted.json').read_text())
 for n,sha in accepted['artifacts'].items():assert digest(fixture/n)==sha
 for n,sha in accepted['installed_artifacts'].items():assert digest(Path(n))==sha
 assert digest(Path('/proc/1/exe'))==accepted['installed_artifacts']['/usr/lib/systemd/systemd']
 assert output(['dpkg-query','-W','-f=${Status} ${Version}','toddy-login-policy'])=='install ok installed 0.1.0-1+toddy1'
 h=Path('/usr/sbin/unix_chkpwd').stat();assert (h.st_uid,h.st_gid,stat.S_IMODE(h.st_mode))==(0,0,0o4755)
 assert 'nosuid' not in output(['findmnt','-n','-o','OPTIONS','/']).split(',')
 subprocess.run(['systemctl','start','dbus.service','systemd-logind.service'],check=True,timeout=30)
 assert output(['systemctl','is-active','systemd-logind.service'])=='active'
 uid=12346;user='toddy-login-policy-probe';home=Path('/home')/user
 assert not home.exists() and not any(r.split(':')[0]==user or r.split(':')[2]==str(uid) for r in Path('/etc/passwd').read_text().splitlines())
 subprocess.run(['useradd','-m','-U','-u',str(uid),'-s','/bin/bash',user],check=True,capture_output=True,timeout=20)
 password=secrets.token_urlsafe(32)
 r=command(['chpasswd','-c','YESCRYPT'],input=user+':'+password+'\n');assert r.returncode==0,'Synthetic yescrypt creation failed; no private output retained'
 def yescrypt():
  row=next(r.split(':') for r in Path('/etc/shadow').read_text().splitlines() if r.startswith(user+':'));assert row[1].startswith('$y$');del row
 yescrypt()
 wrappers=[]
 for service in ['toddy-password','toddy-session']:
  p=Path('/etc/pam.d')/service;assert not p.exists()
  p.write_text('auth include system-auth\naccount include system-account\npassword include system-password\nsession include system-session\n');wrappers.append(p)
 env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8'};runs=[]
 def attempt(label,secret,expected,username=user):
  r=command([str(fixture/'password-consumer'),'/etc/pam.d',username],input=secret+'\n',env=env,user=uid,group=uid,extra_groups=[])
  assert r.returncode==0,'Auth client failed: '+label
  row=json.loads(r.stdout);assert row['start']==row['end']==0
  if expected:assert row['auth']==row['account']==row['credential']==0,'Expected authenticated/account success: '+label
  else:assert row['auth']!=0 or row['account']!=0,'Expected refusal: '+label
  runs.append({'name':label,'exit':0,'pam_result':row,'actor_uid':uid,'expected_authenticated_and_account_accepted':expected})
 attempt('owned-policy-correct-yescrypt',password,True)
 attempt('wrong-password-refused',secrets.token_urlsafe(32),False)
 attempt('empty-password-refused','',False)
 attempt('missing-account-refused',password,False,username='toddy-absent-login-user')
 subprocess.run(['usermod','-L',user],capture_output=True,check=True);attempt('locked-account-refused',password,False)
 subprocess.run(['usermod','-U',user],capture_output=True,check=True);attempt('unlock-recovery',password,True)
 subprocess.run(['chage','-E','1970-01-02',user],capture_output=True,check=True);attempt('expired-account-refused',password,False)
 subprocess.run(['chage','-E','-1',user],capture_output=True,check=True);attempt('expiry-reset-recovery',password,True)
 before=digest(Path('/etc/shadow'))
 stopped=subprocess.Popen([str(fixture/'password-consumer'),'/etc/pam.d',user],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env,user=uid,group=uid,extra_groups=[])
 time.sleep(.05);assert stopped.poll() is None;stopped.terminate();out,err=stopped.communicate(timeout=10)
 assert stopped.returncode==-signal.SIGTERM and not out and digest(Path('/etc/shadow'))==before
 runs.append({'name':'Stop-before-token-no-write','exit':0,'actual_signal_exit':stopped.returncode,'shadow_unchanged':True,'in_flight_PAM_cancellation_claimed':False})
 attempt('fresh-auth-after-stopped-client',password,True)
 newpassword=secrets.token_urlsafe(32)
 before=digest(Path('/etc/shadow'))
 denied=command([str(fixture/'password-change'),user],input=newpassword+'\n',env=env,user=uid,group=uid,extra_groups=[])
 assert denied.returncode==64 and not denied.stdout and digest(Path('/etc/shadow'))==before
 runs.append({'name':'unprivileged-root-token-client-refused','exit':0,'actual_client_exit':64,'shadow_unchanged':True})
 r=command([str(fixture/'password-change'),user],input=newpassword+'\n',env=env);assert r.returncode==0,'Root synthetic PAM token client failed'
 row=json.loads(r.stdout);assert row=={'start':0,'change':0,'end':0};yescrypt()
 runs.append({'name':'system-password-root-owned-PAM-token-change','exit':0,'pam_result':row,'actor_euid':0,'yescrypt_backend':True})
 attempt('old-token-refused-after-PAM-change',password,False);password=newpassword;newpassword=None
 attempt('new-token-authentication-recovery',password,True)
 unit='toddy-login-policy-live'
 r=command(['systemd-run','--quiet','--unit='+unit,'--property=User='+str(uid),'--property=PAMName=toddy-password','/usr/bin/sleep','60']);assert r.returncode==0
 wait_for(lambda: output(['systemctl','show',unit,'--property=MainPID','--value'])!='0')
 assert output(['systemctl','show',unit,'--property=ActiveState','--value'])=='active'
 subprocess.run(['systemctl','stop',unit],check=True,timeout=25)
 assert output(['systemctl','show',unit,'--property=MainPID','--value'])=='0'
 runs.append({'name':'actual-PAMName-shared-session-and-Stop','exit':0,'main_pid_after_Stop':0})
 subprocess.run(['loginctl','terminate-user',str(uid)],capture_output=True,timeout=25)
 wait_for(lambda:not Path('/run/user',str(uid)).exists())
 cycles=[]
 for cycle in [1,2]:
  client=subprocess.Popen([str(fixture/'session-consumer'),'/etc/pam.d',user],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
  # The old qualified client emits a real PAM/logind-ready record, not a fixture.
  import select
  ready=select.select([client.stdout],[],[],25)[0];assert ready,'No PAM session-ready output'
  opened=json.loads(client.stdout.readline());assert opened['phase']=='ready'
  sid=opened['session_id'];assert sid and re.fullmatch('[A-Za-z0-9_-]+',sid)
  props=dict(s.split('=',1) for s in output(['loginctl','show-session',sid,'--property=User','--property=Name','--property=Class','--property=Type','--property=State','--property=Service']).splitlines())
  assert props['User']==str(uid) and props['Name']==user and props['Service']=='toddy-session' and props['State'] in ['active','online']
  runtime=Path('/run/user')/str(uid);assert opened['runtime_dir']==str(runtime)
  st=runtime.stat();assert st.st_uid==uid and stat.S_IMODE(st.st_mode)==0o700
  wait_for(lambda:command(['systemctl','is-active','user@'+str(uid)+'.service']).stdout.strip()=='active')
  wait_for(lambda:(runtime/'bus').is_socket())
  userenv={**env,'HOME':str(home),'USER':user,'LOGNAME':user,'XDG_RUNTIME_DIR':str(runtime),'DBUS_SESSION_BUS_ADDRESS':'unix:path='+str(runtime/'bus')}
  bus=command(['busctl','--user','call','org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','GetId'],user=uid,group=uid,extra_groups=[],env=userenv);assert bus.returncode==0 and re.fullmatch('s "[a-f0-9]+"\n?',bus.stdout)
  out,err=client.communicate('\n',timeout=25);assert client.returncode==0
  closed=json.loads(out.strip());assert closed=={'phase':'closed','close':0,'end':0}
  subprocess.run(['loginctl','terminate-user',str(uid)],capture_output=True,check=True,timeout=25)
  wait_for(lambda:not runtime.exists());wait_for(lambda:command(['loginctl','show-session',sid]).returncode!=0)
  cycles.append({'cycle':cycle,'actual_session':props,'runtime_uid':uid,'runtime_mode':'0700','user_manager_active':True,'user_bus_get_id_exit':0,'bus_id_sha256':hashlib.sha256(bus.stdout.encode()).hexdigest(),'close':closed,'cleanup_and_explicit_terminate_user_verified':True})
 assert cycles[0]['bus_id_sha256']!=cycles[1]['bus_id_sha256']
 password=None
 subprocess.run(['userdel','-r',user],capture_output=True,check=True,timeout=20)
 for p in wrappers:p.unlink()
 assert not home.exists() and not any(r.startswith(user+':') for r in Path('/etc/passwd').read_text().splitlines())
 for n,sha in accepted['installed_artifacts'].items():assert digest(Path(n))==sha
 for n,sha in accepted['artifacts'].items():assert digest(fixture/n)==sha
 raw=json.dumps({'scope':'Actual installed four owned login PAM includes on native kernel: unprivileged yescrypt/auth/refusal/recovery, root-owned password change, PAMName Stop and two PAM/logind/user-bus sessions. Synthetic credentials only; no GDM/greeter/native GNOME/physical acceptance.','kernel':os.uname().release,'pid1':'systemd','fixture_manifest_sha256':digest(fixture/'accepted.json'),'runs':runs,'session_cycles':cycles,'existing_PAM_and_module_artifacts_unchanged':len(accepted['installed_artifacts']),'ephemeral_user_removed':True,'no_credentials_or_hashes_recorded':True},sort_keys=True).encode()
 encoded=base64.b64encode(zlib.compress(raw,9)).decode();chunks=[encoded[i:i+1024] for i in range(0,len(encoded),1024)]
 for i,chunk in enumerate(chunks):print('TODDY_B02_RUNTIME_DATA',i,chunk,flush=True)
 print('TODDY_B02_RUNTIME_RESULT',json.dumps({'kernel':os.uname().release,'all_selected_exits_zero':True,'report_sha256':hashlib.sha256(raw).hexdigest(),'chunks':len(chunks)}),flush=True)
if __name__=='__main__':
 try:main()
 except Exception as error:
  print('TODDY_B02_RUNTIME_FAIL',type(error).__name__,str(error),flush=True)
  raise
