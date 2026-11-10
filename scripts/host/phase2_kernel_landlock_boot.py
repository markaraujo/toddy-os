#!/usr/bin/env python3
"""Boot only the qualified Landlock candidate and diagnostic initramfs, no disks."""
import fcntl,hashlib,json,os
from pathlib import Path
import shlex,subprocess,uuid
import boot_test as boot
import vm,phase2_vm
from probe_grub_media import save,run

def main():
 lock=os.open(vm.VM/'native-boot-test.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600);fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 boot.refuse_running_tests()
 assert not subprocess.check_output(['git','status','--porcelain'],cwd=vm.ROOT,text=True).strip(),'Commit reviewed diagnostic inputs before boot'
 mem=dict(line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines());assert int(mem['MemAvailable'].split()[0])>=4*1024**2
 base=vm.ROOT/'.local/phase2/native-kernel-landlock-1';assert not base.exists(),'Inspect actual existing boot/container; never replay'
 base.mkdir();assert base.resolve()==base
 source=vm.ROOT/'scripts/build/phase2/kernel_landlock_init.c'
 remote=Path('/mnt/lfs/sources/phase2/work/kernel-landlock-1')
 script='''from pathlib import Path
import json
p=Path('/var/log/toddy/phase2');assert (p/'kernel-landlock-boot-prepare-1.exit').read_text().strip()=='0'
print((Path('/mnt/lfs/sources/phase2/work/kernel-landlock-1/boot-probe-1/prepared.json')).read_text())
'''
 built=json.loads(subprocess.check_output(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(script)],text=True));assert built['compile_exit']==0 and built['static_linked'] and built['source_sha256']==boot.digest(source)
 token=built['token'];assert len(token)==32 and all(c in '0123456789abcdef' for c in token)
 save(base/'intent.json',{'source_commit':run('git','rev-parse','HEAD').stdout.strip(),'source_sha256':boot.digest(source),'prepared':built,'scope':'Two diagnostic firmware boots, NO target/builder/physical disks attached. Not Systemd/desktop/installer acceptance.'})
 result={'complete':False,'scope':'Native kernel diagnostic initramfs only; no installed-system/Systemd/desktop/physical hardware acceptance','runs':[]};exitcode=1
 try:
  for name,path,key in [('bzImage',remote/'merged/arch/x86/boot/bzImage','kernel_sha256'),('initramfs.cpio.gz',remote/'boot-probe-1/initramfs.cpio.gz','initramfs_sha256')]:
   with (base/name).open('xb') as f:subprocess.run(phase2_vm.ssh_args()+['cat -- '+shlex.quote(str(path))],stdout=f,check=True,timeout=60)
   assert boot.digest(base/name)==built[key]
  image=run('docker','image','inspect','--format','{{.Id}}',vm.IMAGE).stdout.strip();result['container_image']=image
  common=['--user',f'{os.getuid()}:{os.getgid()}','--cap-drop=ALL','--security-opt=no-new-privileges','--network=none','--read-only']
  hashes=run('docker','run','--rm',*common,image,'sha256sum',boot.CODE,boot.VARS).stdout
  assert {l.split()[1]:l.split()[0] for l in hashes.splitlines()}==boot.FIRMWARE_HASHES
  for firmware in ['bios','uefi']:
   work=base/firmware;work.mkdir();mounts=['-v',f'{base}/bzImage:/media/kernel:ro','-v',f'{base}/initramfs.cpio.gz:/media/initramfs:ro','-v',f'{work}:/work']
   if firmware=='uefi':
    run('docker','run','--rm',*common,*mounts,image,'cp',boot.VARS,'/work/OVMF_VARS.fd');assert boot.digest(work/'OVMF_VARS.fd')==boot.FIRMWARE_HASHES[boot.VARS]
   qemu=['qemu-system-x86_64','-enable-kvm','-machine','q35','-cpu','qemu64','-smp','2','-m','1024','-display','none','-serial','file:/work/serial.log','-monitor','none','-nic','none','-no-reboot','-kernel','/media/kernel','-initrd','/media/initramfs','-append','console=ttyS0,115200 rdinit=/init panic=-1 toddy_probe_mode='+firmware+' toddy_probe_token='+token]
   if firmware=='uefi':qemu+=['-drive',f'if=pflash,format=raw,readonly=on,file={boot.CODE}','-drive','if=pflash,format=raw,file=/work/OVMF_VARS.fd']
   name='toddy-landlock-'+uuid.uuid4().hex[:12]
   args=['docker','create','--name',name,'--label','toddy.boot-test='+name,*common,*mounts,'--device','/dev/kvm','--group-add',str(Path('/dev/kvm').stat().st_gid),'--memory','2g','--cpus','2',image,*qemu]
   save(work/'intent.json',{'argv':args,'timeout_seconds':60});cid=run(*args).stdout.strip();save(work/'container.json',{'id':cid,'name':name})
   try:
    run('docker','start',cid);wait=run('docker','wait',cid,timeout=60);state=json.loads(run('docker','inspect',cid).stdout)[0]['State'];save(work/'exit.json',state)
    assert wait.stdout.strip()=='0' and state['ExitCode']==0 and not state['OOMKilled']
    text=(work/'serial.log').read_text(errors='replace');sentinel='TODDY_LANDLOCK_OK token='+token+' firmware='+firmware
    assert text.splitlines().count(sentinel)==1 and 'TODDY_LANDLOCK_FAIL' not in text and 'Kernel panic' not in text
    lines=[l for l in text.splitlines() if l.startswith('Landlock ABI=')];assert len(lines)==1
    result['runs'].append({'firmware':firmware,'exit':0,'summary':lines[0],'serial_sha256':boot.digest(work/'serial.log'),'kernel_boot_verified':True,'target_disks_attached':False})
   finally:
    terminal=boot.stop_owned_container(cid,name);save(work/'terminal.json',terminal)
    if not terminal['Running']:run('docker','rm',cid)
  assert boot.digest(base/'bzImage')==built['kernel_sha256'] and boot.digest(base/'initramfs.cpio.gz')==built['initramfs_sha256']
  result['complete']=True;exitcode=0
 except BaseException as e:result['error']=str(e);raise
 finally:save(base/'result.json',result);save(base/'driver.exit.json',{'exit':exitcode});print(json.dumps(result))
if __name__=='__main__':main()
