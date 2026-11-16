#!/usr/bin/env python3
"""One-shot exact candidate top-overlay growth; no execution on physical disks."""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import select
import shutil
import socket
import subprocess
import time
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))

import phase2_candidate_vm as candidate
import vm

ROOT=vm.ROOT;WORK=candidate.WORK
SPEC=importlib.util.spec_from_file_location('candidate_geometry',ROOT/'scripts/build/phase2/candidate_target_geometry.py')
geometry=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(geometry)
CONTEXT=WORK/'target-growth-1';GUEST='/opt/toddy-build/scripts/build/phase2/grow_candidate_target.py'
COLD=100*1024**3+512*1024**2


class QMP:
    def __init__(self):
        self.socket=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);self.socket.settimeout(30);self.socket.connect(str(WORK/'qmp.sock'));self.stream=self.socket.makefile('rwb',buffering=0);self.sequence=0
        self.greeting=json.loads(self.stream.readline(1024**2))
        if 'QMP' not in self.greeting:raise ValueError('Actual candidate QMP greeting required')
        self.call('qmp_capabilities')
    def call(self,command,args=None):
        self.sequence+=1;self.stream.write((json.dumps({'execute':command,'id':self.sequence,**({'arguments':args} if args is not None else {})})+'\n').encode())
        while True:
            raw=self.stream.readline(1024**2)
            if not raw:raise ValueError('QMP connection lost; inspect actual disk before any action')
            value=json.loads(raw)
            if value.get('id')==self.sequence:
                if 'error' in value:raise ValueError('QMP refused '+command+': '+value['error'].get('class','unknown'))
                return value['return']
    def block(self,size):
        rows=[row for row in self.call('query-block') if row.get('device')=='lfs']
        if len(rows)!=1:raise ValueError('Exactly one lfs block required')
        image=rows[0].get('inserted',{}).get('image',{})
        if image.get('filename')!='/vm/phase2-candidate/lfs-target.qcow2' or image.get('format')!='qcow2' or image.get('virtual-size')!=size or image.get('backing-filename')!='/vm/phase2/lfs-target.qcow2':raise ValueError('Exact candidate top-overlay/backing/size required')
        return rows[0]
    def close(self):self.stream.close();self.socket.close()


def source_pins():return {name:hashlib.sha256((ROOT/'scripts/build/phase2'/name).read_bytes()).hexdigest() for name in ('grow_candidate_target.py','candidate_target_geometry.py')}

def capacity(free):
    if free-(geometry.NEW-geometry.OLD)<COLD:raise ValueError('Host requires cold100GiB+512MiB PLUS all24GiB growth allowance')


def save(value):candidate.save(CONTEXT/'state.json',value)


def receive(process,timeout=900):
    ready=select.select([process.stdout],[],[],timeout)[0]
    if not ready:raise TimeoutError('Guest snapshot/growth deadline; inspect running operation, never replay')
    raw=process.stdout.readline(4*1024**2)
    if not raw:raise ValueError('Guest ended before a verified growth result')
    return json.loads(raw)


def authorize():
    approval=json.loads((ROOT/'status.json').read_bytes())
    if approval.get('owner_review',{}).get('phase_2_approved') is not True or approval.get('execution_hold'):raise ValueError('Current owner phase authorization required')
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():raise ValueError('Commit reviewed source inputs before growth')


def cold_resize():
    with (vm.VM/'native-boot-test.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state=json.loads((CONTEXT/'state.json').read_bytes())
        if state.get('phase')!='cold-guest-prepared' or state.get('producer_pins')!=source_pins():raise ValueError('Exact cold prepared source/intent required')
        if subprocess.check_output(['docker','ps','-aq','--filter','name=^/'+candidate.NAME+'$'],text=True).strip():raise ValueError('Use authenticated candidate stop before cold resize')
        if candidate.bases()!=state['accepted_backing_identity']:raise ValueError('Cold accepted backing changed')
        disk=WORK/'lfs-target.qcow2'
        if disk.is_symlink() or disk.resolve()!=disk or disk.stat().st_uid!=os.getuid() or disk.stat().st_nlink!=1:raise ValueError('Owned canonical cold overlay required')
        stops=sorted(WORK.glob('stop-*.json'));receipt=json.loads(stops[-1].read_bytes()) if stops else {}
        if receipt.get('phase')!='cold' or receipt.get('accepted_B02_unchanged') is not True or receipt.get('candidate_disks',{}).get('lfs-target.qcow2')!=candidate.identity(disk):raise ValueError('Actual clean cold-stop identity required')
        before=json.loads(candidate.tool('qemu-img','info','--output=json','/vm/phase2-candidate/lfs-target.qcow2').stdout)
        if before.get('format')!='qcow2' or before.get('virtual-size')!=geometry.OLD or before.get('backing-filename')!='/vm/phase2/lfs-target.qcow2':raise ValueError('Exact cold candidate overlay required')
        capacity(shutil.disk_usage(WORK).free);state.update(phase='cold-resize-intended',cold_stop=receipt);save(state)
        result=candidate.tool('qemu-img','resize','/vm/phase2-candidate/lfs-target.qcow2',str(geometry.NEW))
        after=json.loads(candidate.tool('qemu-img','info','--output=json','/vm/phase2-candidate/lfs-target.qcow2').stdout)
        if after.get('virtual-size')!=geometry.NEW or after.get('backing-filename')!=before['backing-filename'] or candidate.bases()!=state['accepted_backing_identity'] or shutil.disk_usage(WORK).free<COLD:raise ValueError('Cold resize postcondition failed; no replay')
        state.update(phase='cold-image-grown',cold_resize_exit=result.returncode,cold_image=after);save(state)


def cold_finish(owned,bases,qmp):
    with (vm.VM/'native-boot-test.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state=json.loads((CONTEXT/'state.json').read_bytes())
        if state.get('phase')!='cold-image-grown' or state.get('producer_pins')!=source_pins() or state['accepted_backing_identity']!=bases:raise ValueError('Exact prior cold image growth required')
        qmp.block(geometry.NEW)
        state.update(phase='cold-guest-finish-intended',restarted_container_id=owned);save(state)
        result=subprocess.run([*candidate.ssh(),'python3 -I -B '+GUEST+' finish-cold'],capture_output=True,text=True)
        (CONTEXT/'cold-finish.stdout').write_text(result.stdout);(CONTEXT/'cold-finish.stderr').write_text(result.stderr)
        if result.returncode!=0:raise ValueError('Cold guest finish failed; inspect actual postconditions, never replay')
        value=json.loads(result.stdout)
        if value.get('event')!='complete' or value['receipt'].get('full_root_changed_paths')!=0 or candidate.bases()!=bases or shutil.disk_usage(WORK).free<COLD:raise ValueError('Cold guest/backing postcondition failed')
        state.update(phase='complete',guest=value,guest_exit=result.returncode,host_free_after=shutil.disk_usage(WORK).free,actual_allocation_after=(WORK/'lfs-target.qcow2').stat().st_blocks*512,accepted_backing_unchanged=True);save(state);print(json.dumps(state,sort_keys=True))

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['inspect','grow','cold-prepare','cold-resize','cold-finish']);args=parser.parse_args()
    if os.geteuid()==0 or vm.VM.resolve()!=vm.VM or WORK.resolve()!=WORK or WORK.is_symlink():raise ValueError('Unprivileged canonical host controller required')
    if args.action!='inspect':authorize()
    if args.action=='cold-resize':cold_resize();return
    owned=candidate.owned();bases=candidate.bases();prepared=json.loads((WORK/'backing.json').read_bytes())
    if prepared['base_identity']!=bases:raise ValueError('Candidate backing custody differs')
    disk=WORK/'lfs-target.qcow2';info=disk.stat()
    if disk.is_symlink() or not disk.is_file() or info.st_uid!=os.getuid() or info.st_nlink!=1:raise ValueError('Owned candidate overlay regular file required')
    qmp=QMP()
    try:
        if args.action=='cold-finish':cold_finish(owned,bases,qmp);return
        if args.action=='inspect':
            print(json.dumps({'container_id':owned,'blocks':qmp.call('query-block'),'host_free_bytes':shutil.disk_usage(WORK).free,'host_cold_reserve':COLD,'growth_allowance':geometry.NEW-geometry.OLD,'prior_growth_exists':CONTEXT.exists(),'live_block_resize_supported':'block_resize' in {row['name'] for row in qmp.call('query-commands')}},sort_keys=True));return
        approval=json.loads((ROOT/'status.json').read_bytes())
        if approval.get('owner_review',{}).get('phase_2_approved') is not True or approval.get('execution_hold'):raise ValueError('Current owner phase authorization required')
        if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():raise ValueError('Commit reviewed source inputs before growth')
        with (vm.VM/'native-boot-test.lock').open('a') as boot_lock:
            fcntl.flock(boot_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            if os.path.lexists(CONTEXT):raise ValueError('Retain and inspect prior operation; no QMP/partition replay')
            before_block=qmp.block(geometry.OLD)
            supported='block_resize' in {row['name'] for row in qmp.call('query-commands')}
            if args.action=='grow' and not supported:raise ValueError('Live QMP resize unsupported; use reviewed cold procedure')
            free=shutil.disk_usage(WORK).free;capacity(free)
            CONTEXT.mkdir(mode=0o700)
            state={'phase':'preflight','container_id':owned,'old_bytes':geometry.OLD,'new_bytes':geometry.NEW,'growth_allowance':geometry.NEW-geometry.OLD,'host_free_before':free,'host_cold_reserve':COLD,'actual_allocation_before':info.st_blocks*512,'overlay_before':candidate.identity(disk),'accepted_backing_identity':bases,'reused_backing_sha256':prepared.get('base_sha256'),'producer_pins':source_pins(),'qmp_before':before_block,'qmp_version':qmp.greeting['QMP']['version'],'controller_pid':os.getpid(),'controller_boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()};save(state)
            with (CONTEXT/'guest.stderr.log').open('xb') as error_log:
                guest=subprocess.Popen([*candidate.ssh(),'python3 -I -B '+GUEST+(' prepare-cold' if args.action=='cold-prepare' else ' serve')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=error_log)
                try:
                    ready=receive(guest)
                    if ready.get('event')!=('cold-prepared' if args.action=='cold-prepare' else 'ready') or ready.get('producer_pins')!=source_pins():raise ValueError('Exact reviewed guest growth source/ready required')
                    state.update(phase='growth-intended',guest_ready=ready);save(state)
                    if args.action=='cold-prepare':
                        guest.stdin.close();code=guest.wait(timeout=30)
                        if code!=0:raise ValueError('Cold guest preparation failed')
                        state.update(phase='cold-guest-prepared',guest_prepare_exit=code);save(state);print(json.dumps(state,sort_keys=True));return
                    if candidate.owned()!=owned or candidate.bases()!=bases:raise ValueError('Candidate ownership/backing changed before QMP')
                    capacity(shutil.disk_usage(WORK).free);qmp.block(geometry.OLD)
                    # This is the ONLY QMP write. Its uncertain reply is never retried.
                    qmp.call('block_resize',{'device':'lfs','size':geometry.NEW})
                    state.update(phase='qmp-grown-guest-pending',qmp_after=qmp.block(geometry.NEW));save(state)
                    guest.stdin.write(b'GROW\n');guest.stdin.flush()
                    result=receive(guest)
                    if result.get('event')!='complete':raise ValueError('Actual guest completed GPT/kernel/ext4 result missing')
                    guest.stdin.close();code=guest.wait(timeout=30)
                    if code!=0:raise ValueError('Actual guest growth exit nonzero')
                    if candidate.owned()!=owned or candidate.bases()!=bases:raise ValueError('Read-only backing custody changed')
                    after=disk.stat()
                    if (after.st_dev,after.st_ino)!=(info.st_dev,info.st_ino) or shutil.disk_usage(WORK).free<COLD:raise ValueError('Overlay identity/absolute host reserve changed')
                    receipt=result['receipt']
                    if receipt.get('new_bytes')!=geometry.NEW or receipt.get('full_root_changed_paths')!=0:raise ValueError('Exact guest geometry/file-integrity receipt required')
                    state.update(phase='complete',guest=result,guest_exit=code,actual_allocation_after=after.st_blocks*512,actual_allocation_delta=after.st_blocks*512-info.st_blocks*512,host_free_after=shutil.disk_usage(WORK).free,overlay_after=candidate.identity(disk),accepted_backing_unchanged=True,qmp_after=qmp.block(geometry.NEW));save(state);print(json.dumps(state,sort_keys=True))
                except BaseException as error:
                    state.update(phase='inspect-no-replay',error_type=type(error).__name__);save(state)
                    if guest.stdin and not guest.stdin.closed:guest.stdin.close()
                    # Never kill a possibly committing guest resize to meet a
                    # host timeout. Its lease/marker survives until it exits.
                    raise
    finally:qmp.close()


if __name__=='__main__':main()
