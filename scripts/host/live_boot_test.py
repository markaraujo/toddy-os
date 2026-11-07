#!/usr/bin/env python3
"""Exercise an actual live console in an isolated BIOS/UEFI CD/USB guest."""
import argparse,base64,fcntl,hashlib,json,os,pathlib,select,shlex,socket,subprocess,tempfile,time,uuid,zlib
import boot_test as boot
import vm
P=pathlib.Path

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('iso',type=P);parser.add_argument('manifest',type=P)
 parser.add_argument('--firmware',choices=['bios','uefi'],required=True)
 parser.add_argument('--medium',choices=['cdrom','usb'],required=True)
 parser.add_argument('--probe',choices=['runtime','security','regex'],default='runtime')
 parser.add_argument('--offline',action='store_true');args=parser.parse_args()
 state={r['id']:r['status'] for r in json.loads((boot.ROOT/'status.json').read_text())['milestones']}
 manifest=json.loads(args.manifest.read_text());validation=manifest.get('validation_only')
 if type(validation) is not bool or not manifest.get('complete'):raise ValueError('Require an actual complete media generation')
 if validation:
  if (state['H09'],state['H10'])!=('completed','in_progress'):raise ValueError('H10 validation gate is not open')
 elif (state['H11'],state['H12'])!=('completed','in_progress'):raise ValueError('H12 release boot gate is not open')
 iso=args.iso.absolute()
 if iso.resolve()!=iso or not iso.is_file() or not iso.is_relative_to(boot.ROOT/'.local'):raise ValueError('Use a physical project-local disposable ISO artifact')
 expected=manifest['media']['sha256']
 if boot.digest(iso)!=expected or iso.stat().st_size!=manifest['media']['bytes']:raise ValueError('Actual media differs from its native generation')
 if subprocess.check_output(['git','status','--porcelain'],cwd=boot.ROOT,text=True).strip():raise ValueError('Commit reviewed inputs before live boot tests')
 lock=os.open(vm.VM/'native-boot-test.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);boot.refuse_running_tests()
 available=int(dict(line.split(':',1) for line in P('/proc/meminfo').read_text().splitlines())['MemAvailable'].split()[0])
 if available<8*1024**2:raise ValueError('Preserve host memory before a 4 GiB live guest')
 folder=vm.VM/'live-tests';folder.mkdir(exist_ok=True)
 if folder.resolve()!=folder:raise ValueError('Redirected live-test storage')
 work=P(tempfile.mkdtemp(prefix=args.firmware+'-'+args.medium+'-',dir=folder))
 token=uuid.uuid4().hex;name='toddy-live-'+token[:16]
 image=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',vm.IMAGE],text=True).strip()
 common=['--user',f'{os.getuid()}:{os.getgid()}','--cap-drop=ALL','--security-opt=no-new-privileges','--read-only',
  '-v',f'{iso}:/media/toddy.iso:ro','-v',f'{work}:/work']
 qemu=['qemu-system-x86_64','-enable-kvm','-machine','q35','-cpu','qemu64','-smp','2','-m','4096',
  '-display','none','-serial','unix:/work/serial.sock,server=on,wait=on','-monitor','none','-no-reboot',
  '-object','rng-random,id=rng0,filename=/dev/urandom','-device','virtio-rng-pci,rng=rng0']
 if args.offline:qemu+=['-nic','none']
 else:qemu+=['-netdev','user,id=n0','-device','virtio-net-pci,netdev=n0']
 if args.medium=='cdrom':qemu+=['-drive','file=/media/toddy.iso,media=cdrom,readonly=on,format=raw','-boot','d']
 else:qemu+=['-device','qemu-xhci,id=xhci','-drive','if=none,id=live,file=/media/toddy.iso,format=raw,readonly=on',
             '-device','usb-storage,drive=live,bootindex=1']
 if args.firmware=='uefi':
  output=subprocess.check_output(['docker','run','--rm','--network=none',*common,image,'sha256sum',boot.CODE,boot.VARS],text=True)
  if {line.split()[1]:line.split()[0] for line in output.splitlines()}!=boot.FIRMWARE_HASHES:raise ValueError('Pinned UEFI firmware changed')
  subprocess.run(['docker','run','--rm','--network=none',*common,image,'cp',boot.VARS,'/work/OVMF_VARS.fd'],check=True)
  qemu+=['-drive',f'if=pflash,format=raw,readonly=on,file={boot.CODE}','-drive','if=pflash,format=raw,file=/work/OVMF_VARS.fd']
 source=(boot.ROOT/'scripts/host'/{'runtime':'live-console-probe.py','security':'live-security-probe.py','regex':'live-regex-probe.py'}[args.probe]).read_bytes()
 encoded=base64.b64encode(zlib.compress(source,9)).decode()
 code="import base64,zlib;exec(zlib.decompress(base64.b64decode("+repr(encoded)+")))"
 command=shlex.join(['python3','-c',code,token,'offline' if args.offline else 'online'])+'\n'
 if len(command)>3800:raise ValueError('Console command exceeds the canonical terminal input budget')
 (work/'probe.py').write_bytes(source);(work/'console-command.txt').write_text(command)
 result={'complete':False,'token':token,'firmware':args.firmware,'medium':args.medium,'offline':args.offline,
  'iso_sha256':expected,'iso_bytes':iso.stat().st_size,'validation_only':validation,'physical_hardware_tested':False,
  'container_image':image,'qemu_arguments':qemu,'probe_sha256':hashlib.sha256(source).hexdigest(),
  'probe_profile':args.probe,'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=boot.ROOT,text=True).strip()}
 def save():
  p=work/'result.json.part';p.write_text(json.dumps(result,indent=2)+'\n');p.replace(work/'result.json')
 cid=None;connection=None;started=time.monotonic();save();print('LIVE_BOOT_WORKSPACE '+str(work),flush=True)
 try:
  cid=subprocess.check_output(['docker','create','--name',name,'--label','toddy.boot-test='+token,*common,
   '--network=none' if args.offline else '--network=bridge','--device','/dev/kvm','--group-add',str(P('/dev/kvm').stat().st_gid),
   '--memory','5g','--cpus','2',image,*qemu],text=True).strip()
  result['container_id']=cid;save();subprocess.run(['docker','start',cid],check=True,stdout=subprocess.DEVNULL)
  connection=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
  for attempt in range(200):
   try:connection.connect(str(work/'serial.sock'));break
   except (FileNotFoundError,ConnectionRefusedError):time.sleep(.1)
  else:raise TimeoutError('Guest serial socket did not appear')
  received=bytearray();sent=False;handshake=False;last_send=0;report=None
  marker=('TODDY_CONSOLE_'+token).encode()
  with (work/'serial.log').open('xb') as log:
   while time.monotonic()-started<360:
    if select.select([connection],[],[],1)[0]:
     data=connection.recv(65536)
     if not data:break
     received.extend(data);log.write(data);log.flush()
    if not handshake and b'root (automatic login)' in received and time.monotonic()-last_send>5:
     connection.sendall(("printf 'TODDY_%s\\n' 'CONSOLE_"+token+"'\n").encode());last_send=time.monotonic()
    if not sent and marker in received:
     handshake=True;connection.sendall(b'stty -echo\n');time.sleep(.1);connection.sendall(command.encode());sent=True
    text=received.decode(errors='replace')
    if 'TODDY_LIVE_ERROR:' in text:raise RuntimeError('Early init entered recovery; inspect preserved serial log')
    if 'TODDY_LIVE_TEST_FAIL ' in text:raise RuntimeError('Native live console probe failed; inspect preserved serial log')
    for line in text.splitlines():
     if 'TODDY_LIVE_TEST_OK ' in line:
      try:report=json.loads(line.split('TODDY_LIVE_TEST_OK ',1)[1])
      except json.JSONDecodeError:continue
    if report is not None and 'native_report' not in result:
     result['native_report']=report;save()
  if report is None:raise TimeoutError('No actual live-console success report')
  if report.get('token')!=token or report.get('firmware')!=args.firmware or report.get('real_console_login') is not True:raise ValueError('Wrong native live result')
  result['native_report']=report;save()
  waited=subprocess.run(['docker','wait',cid],capture_output=True,text=True,timeout=60,check=True)
  if waited.stdout.strip()!='0':raise ValueError('Guest did not power off cleanly')
  actual=json.loads(subprocess.check_output(['docker','inspect',cid],text=True))[0]['State']
  if actual['Running'] or actual['ExitCode']!=0:raise ValueError('QEMU remains active or failed')
  if boot.digest(iso)!=expected:raise ValueError('Live medium changed during volatile-write test')
  result.update(complete=True,container_state=actual,media_unchanged=True,elapsed_seconds=time.monotonic()-started)
 except BaseException as error:
  result['error']=str(error)
  if cid:
   try:result['container_state']=boot.stop_owned_container(cid,token)
   except Exception as e:result['cleanup_uncertain']=str(e)
  raise
 finally:
  if connection:connection.close()
  if cid:
   logs=subprocess.run(['docker','logs',cid],capture_output=True)
   (work/'qemu.log').write_bytes(logs.stdout+logs.stderr)
  if (work/'serial.log').exists():result['serial_sha256']=boot.digest(work/'serial.log')
  save()
if __name__=='__main__':main()
