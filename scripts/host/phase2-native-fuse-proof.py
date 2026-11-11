"""Real installed FUSE helper/owner/refusal/recovery checks in a disposable guest."""
from pathlib import Path
import gzip,hashlib,json,os,re,shutil,signal,stat,subprocess,time

def verify_native_fuse(uid=12402,previous=None):
 assert os.getuid()==0 and os.uname().release=='7.1.8-toddy'
 assert hashlib.sha256(gzip.decompress(Path('/proc/config.gz').read_bytes())).hexdigest()=='952e7d9d6e5c8e523ebf128c220481bc29280424e0686e4b0903b518234bf77b'
 device=subprocess.check_output(['findmnt','-n','-o','SOURCE','/'],text=True).strip();assert re.fullmatch('/dev/[a-z0-9]+',device)
 parent=subprocess.check_output(['lsblk','-ndo','PKNAME',device],text=True).strip()
 assert subprocess.check_output(['lsblk','-dnro','SERIAL','/dev/'+parent],text=True).strip()=='TODDY-BOOT-TEST'
 root=Path('/run/toddy-fuse-drivers');assert not root.exists();root.mkdir(mode=0o755)
 for name,digest in {'native-hello':'56e5870d5edec057dbc4652efacf801182f89dff4e185b5f9189db4a0e275aab','native-test-signals':'c516abc4d2ce3049537b18f1d13e2acfbc7fce04e6395449078ebae406cc7b6b'}.items():
  src=Path('/sources/phase2/work/fuse-1')/name
  assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
  shutil.copyfile(src,root/name);(root/name).chmod(0o755)
 helper=Path('/usr/bin/fusermount3');s=helper.stat();assert (s.st_uid,s.st_gid,stat.S_IMODE(s.st_mode))==(0,0,0o4755)
 conf=Path('/etc/fuse.conf');confsha=hashlib.sha256(conf.read_bytes()).hexdigest()
 assert not any(l.strip()=='user_allow_other' for l in conf.read_text().splitlines())
 fixture=Path('/tmp/toddy-native-fuse-proof');assert not fixture.exists();fixture.mkdir(mode=0o755)
 for name in ['owner','refused']:
  p=fixture/name;p.mkdir(mode=0o755);os.chown(p,uid,uid)
 plain=fixture/'plain-readable';plain.write_text('positive parent access\n');plain.chmod(0o444)
 env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/home/toddy-preview'}
 def run(args,user=uid,timeout=20):
  p=subprocess.run(args,user=user,group=user,extra_groups=[],env=env,cwd=fixture,capture_output=True,text=True,timeout=timeout)
  return {'args':args,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
 result={'scope':'Actual installed FUSE module/device, ordinary UID12402 SUID-helper mount, owner read/unmount, different-UID denial, default allow_other refusal, SIGTERM cleanup and original signals driver in disposable native VM. No physical test.','running_config_sha256':'952e7d9d6e5c8e523ebf128c220481bc29280424e0686e4b0903b518234bf77b','uid':uid,'module_preloaded_by_probe':False,'module_present_before_initial_mount':Path('/sys/module/fuse').exists()}
 child=run(['python3','-c',"from pathlib import Path;print(Path('/proc/self/status').read_text())"]);assert child['exit']==0
 status=dict(l.split(':',1) for l in child['stdout'].splitlines() if ':' in l)
 assert int(status['CapEff'].strip(),16)==0 and status['NoNewPrivs'].strip()=='0';result['ordinary_caller']={'CapEff':status['CapEff'].strip(),'NoNewPrivs':status['NoNewPrivs'].strip()}
 # UID65534 has no owner privileges. Parent access positive control is independent.
 control=run(['cat',str(plain)],65534);assert control['exit']==0;result['other_uid_parent_control']=control
 mount=fixture/'owner';processes=[]
 def mounted():
  p=subprocess.run(['findmnt','-n','-o','FSTYPE,OPTIONS','--mountpoint',str(mount)],capture_output=True,text=True)
  return p.stdout.strip() if p.returncode==0 else None
 def start():
  log=(fixture/('server-'+str(len(processes))+'.log')).open('x');p=subprocess.Popen([str(root/'native-hello'),'-f',str(mount)],user=uid,group=uid,extra_groups=[],env=env,cwd=fixture,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT);processes.append((p,log))
  deadline=time.monotonic()+15
  while time.monotonic()<deadline:
   if mounted():break
   assert p.poll() is None,'Real helper mount failed; inspect server log'
   time.sleep(.1)
  row=mounted();assert row and row.startswith('fuse') and all(v in row for v in ['nosuid','nodev','user_id='+str(uid),'group_id='+str(uid)]),row
  assert p.poll() is None
  return p,row
 try:
  if previous is None:
   initial=mounted();assert initial is None
   p,row=start();result['first_owner_mount']=row
   assert Path('/sys/module/fuse').is_dir() and stat.S_ISCHR(Path('/dev/fuse').stat().st_mode)
   result['device_mode']=oct(stat.S_IMODE(Path('/dev/fuse').stat().st_mode));assert result['device_mode']=='0o666'
   read=run(['cat',str(mount/'hello')]);assert read['exit']==0 and read['stdout']=='Hello World!\n';result['owner_read']=read
   denied=run(['cat',str(mount/'hello')],65534);assert denied['exit']!=0 and 'Permission denied' in denied['stderr'];result['other_uid_read_denied']=denied
   denied=run(['fusermount3','-u',str(mount)],65534);assert denied['exit']!=0 and mounted();result['other_uid_unmount_denied']=denied
   assert run(['cat',str(mount/'hello')])['stdout']=='Hello World!\n'
   refused=run([str(root/'native-hello'),'-f','-o','allow_other',str(fixture/'refused')]);assert refused['exit']!=0 and 'user_allow_other' in refused['stderr'];result['allow_other_refused']=refused
   assert subprocess.run(['findmnt','--mountpoint',str(fixture/'refused')],capture_output=True).returncode!=0
   unmount=run(['fusermount3','-u',str(mount)]);assert unmount['exit']==0 and p.wait(timeout=15)==0 and not mounted();result['owner_unmount']=unmount
  else:
   assert previous['running_config_sha256']==result['running_config_sha256'] and previous['uid']==uid
   for key in ['first_owner_mount','device_mode','owner_read','other_uid_read_denied','other_uid_unmount_denied','allow_other_refused','owner_unmount']:
    result[key]=previous[key]
   result['reused_evidence']='native-fuse-portal-runtime-2 authenticated partial native report; same unchanged backing/package/kernel inputs'
  p,row=start();ready=run(['cat',str(mount/'hello')]);assert ready['exit']==0 and ready['stdout']=='Hello World!\n'
  p.send_signal(signal.SIGTERM);code=p.wait(timeout=15);result['sigterm_cleanup_exit']=code;result['sigterm_mount_absent']=not mounted()
  # Fuse3.18.2 exit_handler records SIGTERM15; loop_mt returns it and helper.c
  # maps nonzero to8 before fuse_unmount. This is a signal exit, not success0.
  assert code==8 and result['sigterm_mount_absent'],('SIGTERM native status/cleanup',code,mounted())
  signals=run([str(root/'native-test-signals')],timeout=20);assert signals['exit']==0;result['original_upstream_signals']=signals
  assert not mounted() and not any(' /tmp/fuse_test_' in l or ' /tmp/toddy-native-fuse-proof/' in l for l in Path('/proc/self/mountinfo').read_text().splitlines())
  assert hashlib.sha256(conf.read_bytes()).hexdigest()==confsha;result['configuration_unchanged']=True;result['all_selected_exits_zero']=True
 except Exception as error:
  import traceback
  result['traceback']=traceback.format_exc()
  result.update(all_selected_exits_zero=False,error={'type':type(error).__name__,'message':str(error)})
 finally:
  for p,log in processes:
   if p.poll() is None:p.terminate();p.wait(timeout=15)
   log.close()
  result['server_logs']={p.name:p.read_text() for p in fixture.glob('server-*.log')}
 return result
