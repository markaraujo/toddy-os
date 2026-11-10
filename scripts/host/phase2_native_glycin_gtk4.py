#!/usr/bin/env python3
"""Cold test the new companion only; preserve builder and accepted core evidence."""
from datetime import datetime,timezone
import fcntl,hashlib,json,os,shlex,shutil,subprocess,sys,uuid
from pathlib import Path
import boot_test as boot
import phase2_vm,vm
from phase2_native_glycin import compressed_payload
from phase2_native_report import decode

def run(args,**kwargs):return subprocess.run(args,check=True,text=True,**kwargs)
def main():
 root=phase2_vm.ROOT;work=phase2_vm.WORK;context=root/'.local/phase2/native-glycin-gtk4-runtime-1'
 assert not context.exists(),'Reconcile actual operation; never replay'
 assert not subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip()
 assert shutil.disk_usage(root).free>=100*1024**3+512*1024**2
 lock=open(vm.VM/'native-boot-test.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);boot.refuse_running_tests()
 code="""from pathlib import Path
import fcntl,hashlib,json
f=open('/var/log/toddy/build/build.lock','a');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
l=Path('/var/log/toddy/phase2');assert (l/'glycin-gtk4-1.exit').read_text().strip()=='0'
r=json.loads((l/'glycin-gtk4-native-fixture.json').read_text());assert r['state']=='complete'
for name,sha in r['stage_sha256'].items():assert hashlib.sha256((Path(r['fixture'])/'stage'/name).read_bytes()).hexdigest()==sha
for name,sha in r['installed_core_sha256'].items():assert hashlib.sha256((Path('/mnt/lfs')/name.lstrip('/')).read_bytes()).hexdigest()==sha
print(json.dumps(r))
"""
 accepted=json.loads(subprocess.check_output(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(code)],text=True))
 body=(root/'scripts/host/phase2-native-glycin-gtk4-probe.py').read_text()
 for name,value in [('CONSUMER_SOURCE',(root/'scripts/build/phase2/glycin-gtk4-native-consumer.py').read_text()),('ACCEPTED_FIXTURE',accepted)]:
  assert body.count(name+' = None')==1;body=body.replace(name+' = None',name+' = '+repr(value))
 probe=body.encode();bootstrap=compressed_payload(probe);context.mkdir()
 state={'scope':'Only native Glycin GTK4 companion conversion; no desktop/G2 acceptance','commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'started_utc':datetime.now(timezone.utc).isoformat(),'controller_pid':os.getpid(),'controller_boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'controller_start_ticks':Path('/proc/self/stat').read_text().split()[21],'accepted':accepted,'probe_sha256':hashlib.sha256(probe).hexdigest(),'payload_sha256':hashlib.sha256(bootstrap).hexdigest(),'phase':'prepared'}
 def save():
  part=context/'result.json.part';assert not part.exists();part.write_text(json.dumps(state,indent=2)+'\n');part.replace(context/'result.json');print(json.dumps({'phase':state['phase'],'context':str(context)}),flush=True)
 save()
 with (context/'builder-stop.log').open('x') as log:
  state['phase']='stopping-builder';save();run([sys.executable,str(root/'scripts/host/phase2_vm.py'),'stop'],stdout=log,stderr=subprocess.STDOUT)
 assert not subprocess.check_output(['docker','ps','-q','--filter','name=^/'+phase2_vm.NAME+'$'],text=True).strip()
 state['phase']='builder-stopped';save();source=work/'lfs-target.qcow2';assert source.is_file() and not source.is_symlink();identity=phase2_vm.backing_identity(source);state['source_identity']=identity
 image=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',vm.IMAGE],text=True).strip();run_id=uuid.uuid4().hex
 common=['--user',f'{os.getuid()}:{os.getgid()}','--cap-drop=ALL','--security-opt=no-new-privileges','--network=none','--read-only','-v',f'{vm.VM}:/vm:ro','-v',f'{context}:/work']
 with (context/'prepare.log').open('x') as log:
  run(['docker','run','--rm',*common,image,'qemu-img','check','/vm/phase2/lfs-target.qcow2'],stdout=log,stderr=subprocess.STDOUT)
  run(['docker','run','--rm',*common,image,'qemu-img','create','-f','qcow2','-F','qcow2','-b','/vm/phase2/lfs-target.qcow2','/work/target.qcow2'],stdout=log,stderr=subprocess.STDOUT)
 payloads={'systemd.extra-unit.toddy-boot-probe.service':(root/'scripts/host/boot-probe.service').read_bytes(),'systemd.unit-dropin.multi-user.target':(root/'scripts/host/boot-probe.target.conf').read_bytes(),'toddy.boot-probe':bootstrap}
 qemu=boot.qemu_arguments('bios',payloads);qemu[qemu.index('-cpu')+1]='host';qemu[qemu.index('-smp')+1]='4';qemu[qemu.index('-m')+1]='4096'
 name='toddy-b02-native-'+run_id[:12];command=['docker','create','--name',name,'--label','toddy.boot-test='+run_id,*common,'--device','/dev/kvm','--group-add',str(Path('/dev/kvm').stat().st_gid),'--memory','5g','--cpus','4',image,*qemu]
 cid=subprocess.check_output(command,text=True).strip();state.update(phase='native-running',container_id=cid,container_name=name,run_id=run_id,command=command);save()
 with (context/'qemu.log').open('x') as log:run(['docker','start',cid],stdout=log,stderr=subprocess.STDOUT)
 try:
  waited=subprocess.run(['docker','wait',cid],capture_output=True,text=True,timeout=240);(context/'docker-wait.json').write_text(json.dumps({'exit':waited.returncode,'stdout':waited.stdout,'stderr':waited.stderr},indent=2)+'\n');waited.check_returncode();assert waited.stdout.strip()=='0'
 finally:state['container_final_state']=boot.stop_owned_container(cid,run_id);state['phase']='native-stopped';save()
 assert phase2_vm.backing_identity(source)==identity;state['backing_unchanged']=True;save()
 report,summary,recovered=decode((context/'serial.log').read_text(errors='replace'));(context/'native-report.json').write_text(json.dumps(report,indent=2)+'\n')
 state.update(phase='native-report-recorded',summary=summary,recovered_protocol_markers=recovered,native_selected_passed=summary['all_selected_exits_zero']);save();assert summary['all_selected_exits_zero'],'Native failure retained, not qualified'
if __name__=='__main__':main()
