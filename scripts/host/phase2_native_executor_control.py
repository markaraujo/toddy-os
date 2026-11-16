#!/usr/bin/env python3
"""One new disposable B04 native control qualification, never a prior job replay."""
from datetime import datetime, timezone
import argparse
import base64
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import uuid
import zlib
import boot_test as boot
from phase2_native_glycin import compressed_payload
from phase2_native_report import decode
import phase2_vm
import vm

ROOT=phase2_vm.ROOT


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--generation',required=True,type=int)
    p.add_argument('--slice',choices=['control','owner','broker'],default='control')
    args=p.parse_args()
    assert 1<=args.generation<=100
    context=ROOT/('.local/phase2/native-executor-'+args.slice+'-'+str(args.generation))
    assert not context.exists(), 'Inspect this actual operation; never redispatch a context'
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip(), 'Commit reviewed inputs first'
    assert shutil.disk_usage(ROOT).free>=100*1024**3+512*1024**2, 'Native overlay reserve required'
    lock=open(vm.VM/'native-boot-test.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    boot.refuse_running_tests();phase2_vm.require_quiescent()
    baseline=json.loads((ROOT/'docs/evidence/B02-completion-stop.json').read_text())
    for name,row in baseline['cold_disks'].items():
        path=phase2_vm.WORK/name
        assert path.is_file() and not path.is_symlink() and phase2_vm.backing_identity(path)==row, 'Cold disk changed; reconcile instead of boot'
    files={}
    for name in ['service.py','store.py','operations.py','command_child.py','linux_identity.py','native_backends.py','policy.py','owner_policy.py','session_identity.py','io.github.markaraujo.Toddy.Executor1.xml']:
        files[name]=(ROOT/'runtime/executor'/name).read_text()
    packed=zlib.compress(json.dumps(files,sort_keys=True).encode(),9)
    parts=[packed[i:i+8192] for i in range(0,len(packed),8192)]
    manifest={'sha256':hashlib.sha256(packed).hexdigest(),'chunks':len(parts),'packaging':{}}
    for source,destination in [('toddy-executor.service','/etc/systemd/system/toddy-executor.service'),
            ('io.github.markaraujo.Toddy.Executor.conf','/etc/dbus-1/system.d/io.github.markaraujo.Toddy.Executor.conf'),
            ('io.github.markaraujo.Toddy.Owner.policy','/usr/share/polkit-1/actions/io.github.markaraujo.Toddy.Owner.policy')]:
        manifest['packaging'][source]={'path':destination,'text':(ROOT/'runtime/executor/packaging'/source).read_text()}
    auxiliary=None
    if args.slice=='broker':
        bundle={}
        for name in ['broker/service.py','broker/core.py','broker/protocol.py','broker/profiles.py','broker/tasks.py',
                     'broker/io.github.markaraujo.Toddy.Service1.xml','broker/engine.py','broker/configured_engine.py','broker/text.py',
                     'connections/secret_store.py','local/server.py','local/managed.py','shared/json.py','tools/native.py','tools/child.py','tools/scoped.py','tools/scoped_child.py']:
            bundle['/usr/lib/toddy/'+name]=(ROOT/'runtime'/name).read_text()
        for name in ['profile.schema.json','local-model.lock.json',*[str(p.relative_to(ROOT/'config/phase2')) for p in (ROOT/'config/phase2/profile').iterdir() if p.is_file() and p.suffix in ('.md','.json')]]:
            bundle['/usr/share/toddy/'+name]=(ROOT/'config/phase2'/name).read_text()
        for source,destination in [('toddy-agent.service','/usr/lib/systemd/user/toddy-agent.service'),
               ('io.github.markaraujo.Toddy.Service.service','/usr/share/dbus-1/services/io.github.markaraujo.Toddy.Service.service')]:
            bundle[destination]=(ROOT/'runtime/broker/packaging'/source).read_text()
        packet=zlib.compress(json.dumps({'bundle':bundle,'hook':(ROOT/'scripts/host/phase2-native-broker-hook.py').read_text()},sort_keys=True).encode(),9)
        assert len(packet)<=1024**2
        manifest['broker']={'sha256':hashlib.sha256(packet).hexdigest(),'bytes':len(packet),'serial':'TODDY-BROKER-INPUTS'}
        auxiliary=b'TODDY_NATIVE_INPUTS_V1\0'+len(packet).to_bytes(8,'big')+hashlib.sha256(packet).digest()+packet
        auxiliary+=b'\0'*((-len(auxiliary))%512)
    extra={'toddy.executor.manifest':json.dumps(manifest,sort_keys=True).encode()}
    extra.update({'toddy.executor.input'+str(i):data for i,data in enumerate(parts)})
    unit=(ROOT/'scripts/host/boot-probe.service').read_bytes().replace(b'TimeoutStartSec=180',b'TimeoutStartSec=300')
    unit+=b''.join(('LoadCredential='+name+'\n').encode() for name in sorted(extra))
    probe=(ROOT/('scripts/host/phase2-native-executor-'+('owner' if args.slice=='broker' else args.slice)+'-probe.py')).read_bytes()
    payloads={'systemd.extra-unit.toddy-boot-probe.service':unit,
              'systemd.unit-dropin.multi-user.target':(ROOT/'scripts/host/boot-probe.target.conf').read_bytes(),
              'toddy.boot-probe':compressed_payload(probe)}
    qemu=boot.qemu_arguments('bios',payloads)
    firmware_bytes=sum(len(base64.b64encode(data)) for data in payloads.values())
    for name,data in sorted(extra.items()):
        encoded=base64.b64encode(data).decode();assert len(encoded)<=16384
        firmware_bytes+=len(encoded)
        qemu+=['-smbios','type=11,value=io.systemd.credential.binary:'+name+'='+encoded]
    assert firmware_bytes<=48*1024,'Firmware input budget exceeded: use read-only auxiliary transport'
    if auxiliary is not None:
        qemu+=['-drive','file=/work/broker-input.raw,if=none,id=brokerinput,format=raw,readonly=on',
               '-device','virtio-blk-pci,drive=brokerinput,serial=TODDY-BROKER-INPUTS']
    qemu[qemu.index('-cpu')+1]='host';qemu[qemu.index('-smp')+1]='4';qemu[qemu.index('-m')+1]='4096'
    image=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',vm.IMAGE],text=True).strip()
    context.mkdir(mode=0o700)
    if auxiliary is not None:
        datafile=context/'broker-input.raw';datafile.write_bytes(auxiliary);datafile.chmod(0o400)
    state={'story':'B04','scope':'Disposable source-stage native owner/executor control qualification; no package/image acceptance',
           'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
           'started_utc':datetime.now(timezone.utc).isoformat(),'controller_pid':os.getpid(),
           'controller_boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
           'controller_start_ticks':Path('/proc/self/stat').read_text().split()[21],
           'phase':'prepared','probe_sha256':hashlib.sha256(probe).hexdigest(),
           'inputs_sha256':manifest['sha256'],'cold_disks':baseline['cold_disks'],
           'firmware_encoded_bytes':firmware_bytes,'auxiliary_sha256':hashlib.sha256(auxiliary).hexdigest() if auxiliary else None}
    def save():
        part=context/'result.json.part';assert not part.exists()
        part.write_text(json.dumps(state,indent=2)+'\n');part.replace(context/'result.json')
        print(json.dumps({'phase':state['phase'],'context':str(context)}),flush=True)
    save()
    common=['--user',f'{os.getuid()}:{os.getgid()}','--cap-drop=ALL','--security-opt=no-new-privileges',
            '--network=none','--read-only','-v',f'{vm.VM}:/vm:ro','-v',f'{context}:/work']
    with (context/'prepare.log').open('x') as log:
        for command in [['qemu-img','check','/vm/phase2/lfs-target.qcow2'],
                        ['qemu-img','create','-f','qcow2','-F','qcow2','-b','/vm/phase2/lfs-target.qcow2','/work/target.qcow2']]:
            subprocess.run(['docker','run','--rm',*common,image,*command],check=True,stdout=log,stderr=subprocess.STDOUT)
    run_id=uuid.uuid4().hex;name='toddy-b04-native-'+run_id[:12]
    command=['docker','create','--name',name,'--label','toddy.boot-test='+run_id,*common,'--device','/dev/kvm',
             '--group-add',str(Path('/dev/kvm').stat().st_gid),'--memory','5g','--cpus','4',image,*qemu]
    cid=subprocess.check_output(command,text=True).strip()
    state.update(phase='native-created',container_id=cid,container_name=name,run_id=run_id);save()
    subprocess.run(['docker','start',cid],check=True,capture_output=True)
    state['phase']='native-running';save()
    try:
        waited=subprocess.run(['docker','wait',cid],text=True,capture_output=True,timeout=420)
        state['docker_wait']={'exit':waited.returncode,'stdout':waited.stdout,'stderr':waited.stderr}
        waited.check_returncode();assert waited.stdout.strip()=='0', 'Actual QEMU exit nonzero'
    finally:
        state['container_final_state']=boot.stop_owned_container(cid,run_id)
        state['phase']='native-stopped';save()
    for name,row in baseline['cold_disks'].items():assert phase2_vm.backing_identity(phase2_vm.WORK/name)==row
    if auxiliary is not None:
        with (context/'broker-input.raw').open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==state['auxiliary_sha256']
    state['backing_unchanged']=True
    serial=(context/'serial.log').read_text(errors='replace')
    report,summary,recovered=decode(serial)
    (context/'native-report.json').write_text(json.dumps(report,indent=2)+'\n')
    state.update(phase='native-report-recorded',summary=summary,recovered_protocol_markers=recovered)
    save()
    assert summary['all_selected_exits_zero'], 'Retained actual failure; not accepted'
    state['phase']='native-control-verified';save()


if __name__=='__main__':main()
