#!/usr/bin/env python3
"""New candidate builder overlays; accepted B02 and foundation stay read-only."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import uuid

import vm
import phase2_vm

ROOT=vm.ROOT
WORK=vm.VM/'phase2-candidate'
NAME='toddy-phase2-candidate'
RESERVE=100*1024**3+512*1024**2
SCRATCH_BYTES=16*1024**3


def run(*args,**kwargs):
    return subprocess.run(args,check=True,**kwargs)


def identity(path):
    return phase2_vm.backing_identity(path)


def bases():
    foundation=json.loads((vm.VM/'phase2/backing.json').read_text())['disks']
    assert set(foundation)=={'builder-base.img','builder.qcow2','lfs-target.qcow2','seed.img'}
    for name,row in foundation.items():
        path=vm.VM/name
        assert path.is_file() and not path.is_symlink() and identity(path)==row['identity'],'Foundation backing changed'
    recorded=json.loads((ROOT/'docs/evidence/B02-completion-stop.json').read_text())['cold_disks']
    for name,expected in recorded.items():
        path=vm.VM/'phase2'/name
        assert path.is_file() and not path.is_symlink() and path.resolve()==path
        assert identity(path)==expected,'Accepted B02 backing changed; reconcile before proceeding'
    return recorded


def tool(*args):
    return run('docker','run','--rm','--user',f'{os.getuid()}:{os.getgid()}',
        '--cap-drop=ALL','--security-opt=no-new-privileges','--network=none','--read-only',
        '-v',f'{vm.VM}:/vm:ro','-v',f'{WORK}:/vm/phase2-candidate',vm.IMAGE,*args,
        capture_output=True,text=True)


def ssh():
    return ['ssh','-i',str(vm.VM/'id_ed25519'),'-p','2223','-o','BatchMode=yes',
        '-o','ConnectTimeout=10','-o','StrictHostKeyChecking=accept-new',
        '-o',f'UserKnownHostsFile={WORK}/known_hosts','root@127.0.0.1']


def owned():
    """Never send root SSH commands to another VM sharing the historical port."""
    result=run('docker','inspect',NAME,capture_output=True,text=True)
    rows=json.loads(result.stdout)
    assert len(rows)==1
    row=rows[0]
    assert row['Name']=='/'+NAME and row['State']['Running'] is True
    assert row['Config']['Labels'].get('toddy.candidate')=='phase2-candidate'
    mounts={m['Source']:m for m in row['Mounts'] if m['Type']=='bind'}
    assert mounts[str(vm.VM)]['Destination']=='/vm' and mounts[str(vm.VM)]['RW'] is False
    assert mounts[str(WORK)]['Destination']=='/vm/phase2-candidate' and mounts[str(WORK)]['RW'] is True
    ports=row['NetworkSettings']['Ports']['2223/tcp']
    assert ports==[{'HostIp':'127.0.0.1','HostPort':'2223'}]
    command=row['Config']['Cmd']
    for name in ('builder.qcow2','lfs-target.qcow2'):
        assert any(value.startswith('file=/vm/phase2-candidate/'+name+',') for value in command)
    return row['Id']


def save(path,value):
    part=path.with_suffix('.part')
    assert not part.exists()
    with part.open('x') as stream:
        json.dump(value,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    os.replace(part,path)
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','start','ssh','stop','inspect'])
    parser.add_argument('command',nargs=argparse.REMAINDER)
    args=parser.parse_args()
    assert os.geteuid()!=0 and vm.VM.resolve()==vm.VM and not vm.VM.is_symlink()
    approval=json.loads((ROOT/'status.json').read_text())['owner_review']
    assert approval['phase_2_approved'] and (ROOT/approval['approval_evidence']).is_file()
    if args.action=='ssh':
        owned();bases();run(*ssh(),*args.command);return
    if args.action=='inspect':
        run('docker','ps','-a','--filter','name=^/'+NAME+'$','--format','{{.Names}} {{.Status}}')
        if (WORK/'backing.json').is_file():print((WORK/'backing.json').read_text())
        return
    if args.action=='stop':
        owned()
        run(*ssh(),'poweroff')
        stopped=run('docker','wait',NAME,capture_output=True,text=True)
        assert stopped.stdout.strip()=='0','Retain nonzero candidate exit for diagnosis'
        run('docker','rm',NAME)
        original=json.loads((WORK/'backing.json').read_text())['base_identity']
        assert bases()==original
        save(WORK/('stop-'+str(time.time_ns())+'.json'),{'phase':'cold','accepted_B02_unchanged':True,
            'candidate_disks':{n:identity(WORK/n) for n in ('builder.qcow2','lfs-target.qcow2')}})
        return
    original=bases()
    # Shared native boot lock also excludes verified cold checkpoint custody.
    lock=open(vm.VM/'native-boot-test.lock','a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    phase2_vm.require_quiescent()
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip(),'Commit reviewed candidate inputs first'
    required=RESERVE+(SCRATCH_BYTES if args.action=='prepare' else 0)
    assert shutil.disk_usage(ROOT).free>=required,'Candidate reserve/capacity required'
    if args.action=='prepare':
        assert not WORK.exists(),'Inspect existing candidate; never repeat preparation'
        WORK.mkdir(mode=0o700)
        record={'scope':'New writable candidate over accepted read-only B02; no acceptance',
            'operation_id':uuid.uuid4().hex,'controller_pid':os.getpid(),
            'controller_boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'controller_start_ticks':Path('/proc/self/stat').read_text().split()[21],
            'producer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'base_identity':original,'base_sha256':{},'checks':{},'phase':'preparing'}
        save(WORK/'prepare.json',record)
        for name in ('builder.qcow2','lfs-target.qcow2'):
            checked=tool('qemu-img','check','/vm/phase2/'+name)
            with (vm.VM/'phase2'/name).open('rb') as stream:
                record['base_sha256'][name]=hashlib.file_digest(stream,'sha256').hexdigest()
            assert bases()==original
            record['checks'][name]=checked.stdout
            tool('qemu-img','create','-f','qcow2','-F','qcow2','-b','/vm/phase2/'+name,'/vm/phase2-candidate/'+name)
            save(WORK/'prepare.json',record)
        scratch=WORK/'qt-raster-work.raw'
        fd=os.open(scratch,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        try:os.posix_fallocate(fd,0,SCRATCH_BYTES);os.fsync(fd)
        finally:os.close(fd)
        record.update(phase='prepared',scratch={'identity':identity(scratch),'serial':'TODDY-QT-RASTER-1',
            'filesystem_created':False,'mount':'/mnt/toddy-qt-raster-1'})
        save(WORK/'backing.json',record)
        return
    record=json.loads((WORK/'backing.json').read_text())
    assert record['phase']=='prepared' and record['base_identity']==original
    memory={line.split(':',1)[0]:line.split(':',1)[1].strip().split()[0]
            for line in Path('/proc/meminfo').read_text().splitlines()}
    assert int(memory['MemAvailable'])*1024>=14*1024**3,'Candidate VM RAM plus overhead unavailable'
    for name in ('builder.qcow2','lfs-target.qcow2','qt-raster-work.raw'):
        assert (WORK/name).is_file() and not (WORK/name).is_symlink()
    # Scratch mtime changes after use; its path/size/UID and fixed serial are
    # rechecked inside the guest before any explicit formatting/mount action.
    assert (WORK/'qt-raster-work.raw').stat().st_size==SCRATCH_BYTES
    actual=identity(WORK/'qt-raster-work.raw')
    assert all(actual[k]==record['scratch']['identity'][k] for k in ('device','inode','bytes'))
    assert (WORK/'qt-raster-work.raw').stat().st_uid==os.getuid()
    run('docker','run','-d','--name',NAME,'--label','toddy.candidate=phase2-candidate',
        '--user',f'{os.getuid()}:{os.getgid()}','--device','/dev/kvm',
        '--group-add',str(Path('/dev/kvm').stat().st_gid),'--cap-drop=ALL',
        '--security-opt=no-new-privileges','--memory','14g','--cpus','12',
        '-p','127.0.0.1:2223:2223','-v',f'{vm.VM}:/vm:ro','-v',f'{WORK}:/vm/phase2-candidate',vm.IMAGE,
        'qemu-system-x86_64','-enable-kvm','-machine','q35','-cpu','host','-smp','12','-m','12288',
        '-display','none','-serial','file:/vm/phase2-candidate/serial.log',
        '-qmp','unix:/vm/phase2-candidate/qmp.sock,server=on,wait=off',
        '-drive','file=/vm/phase2-candidate/builder.qcow2,if=none,id=builder,format=qcow2',
        '-device','virtio-blk-pci,drive=builder,serial=TODDY-BUILDER',
        '-drive','file=/vm/phase2-candidate/lfs-target.qcow2,if=none,id=lfs,format=qcow2,discard=unmap',
        '-device','virtio-blk-pci,drive=lfs,serial=TODDY-LFS-TARGET',
        '-drive','file=/vm/phase2-candidate/qt-raster-work.raw,if=none,id=qtwork,format=raw,discard=unmap',
        '-device','virtio-blk-pci,drive=qtwork,serial=TODDY-QT-RASTER-1',
        '-drive','file=/vm/seed.img,if=virtio,format=raw,readonly=on',
        '-netdev','user,id=net0,hostfwd=tcp:0.0.0.0:2223-:22',
        '-device','virtio-net-pci,netdev=net0')
    assert bases()==original


if __name__=='__main__':main()
