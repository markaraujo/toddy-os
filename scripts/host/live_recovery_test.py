#!/usr/bin/env python3
"""Verify actual early rescue, missing media and corrupted media in disposable VMs."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import select
import shutil
import socket
import subprocess
import tempfile
import time
import uuid

import boot_test as boot
import vm


def number(data):
    little, big = int.from_bytes(data[:4], 'little'), int.from_bytes(data[4:8], 'big')
    if little != big:
        raise ValueError('ISO dual-endian field differs')
    return little


def extent(iso, parts):
    """Read this native ISO's inline Rock Ridge names; reject multi-extents."""
    with iso.open('rb') as stream:
        stream.seek(16 * 2048)
        pvd = stream.read(2048)
        if pvd[:7] != b'\x01CD001\x01':
            raise ValueError('Expected primary ISO9660 descriptor')
        record = pvd[156:190]
        for part in parts:
            if not record[25] & 2:
                raise ValueError('Non-directory ISO path component')
            start, size = number(record[2:10]) * 2048, number(record[10:18])
            if size > 1024**2 or start + size > iso.stat().st_size:
                raise ValueError('Unexpected ISO directory size/extent')
            stream.seek(start); directory = stream.read(size); matches = []; offset = 0
            while offset < size:
                length = directory[offset]
                if not length:
                    offset = ((offset // 2048) + 1) * 2048
                    continue
                candidate = directory[offset:offset+length]
                if length < 34 or len(candidate) != length:
                    raise ValueError('Invalid directory record')
                name = candidate[33:33+candidate[32]].decode('ascii').split(';')[0]
                extension = 33 + candidate[32] + (candidate[32] % 2 == 0)
                names = []
                while extension + 4 <= length:
                    field = candidate[extension:]
                    size_field = field[2]
                    if size_field < 4 or extension + size_field > length:
                        raise ValueError('Invalid ISO system-use field')
                    if field[:2] == b'NM':
                        if size_field < 5 or field[3:5] != b'\x01\x00':
                            raise ValueError('Unsupported split Rock Ridge name')
                        names.append(field[5:size_field].decode('ascii'))
                    extension += size_field
                if len(names) > 1:
                    raise ValueError('Ambiguous Rock Ridge name')
                if (names[0] == part if names else name == part.upper()):
                    matches.append(candidate)
                offset += length
            if len(matches) != 1:
                raise ValueError('Missing/ambiguous ISO path: ' + part)
            record = matches[0]
        start, size = number(record[2:10]) * 2048, number(record[10:18])
        if record[25] & (2 | 128) or start + size > iso.stat().st_size:
            raise ValueError('Unsupported ISO payload extent')
        return start, size


def payload(iso, parts, expected, destination=None):
    start, size = extent(iso, parts)
    digest = hashlib.sha256()
    output = destination.open('xb') if destination else None
    try:
        with iso.open('rb') as stream:
            stream.seek(start); remaining = size
            while remaining:
                data = stream.read(min(1024**2, remaining))
                if not data:
                    raise ValueError('Truncated ISO payload')
                remaining -= len(data); digest.update(data)
                if output:
                    output.write(data)
        if digest.hexdigest() != expected:
            raise ValueError('ISO payload does not match bound artifact')
    finally:
        if output:
            output.close()
    return start, size


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('iso', type=Path); parser.add_argument('manifest', type=Path)
    parser.add_argument('--case', required=True, choices=['rescue', 'missing', 'corrupt'])
    args = parser.parse_args()
    states = {r['id']: r['status'] for r in json.loads((boot.ROOT/'status.json').read_text())['milestones']}
    if (states['H11'], states['H12']) != ('completed', 'in_progress'):
        raise ValueError('Require accepted H11 and active H12')
    if subprocess.check_output(['git','status','--porcelain'],cwd=boot.ROOT,text=True).strip():
        raise ValueError('Commit reviewed inputs before recovery tests')
    iso = args.iso.absolute(); manifest = json.loads(args.manifest.read_text())
    if (iso.resolve() != iso or not iso.is_relative_to(boot.ROOT/'.local')
            or manifest.get('complete') is not True or manifest.get('validation_only') is not False
            or boot.digest(iso) != manifest['media']['sha256'] or iso.stat().st_size != manifest['media']['bytes']):
        raise ValueError('Require unchanged final native ISO generation')
    lock = os.open(vm.VM/'native-boot-test.lock', os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW, 0o600)
    fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB); boot.refuse_running_tests()
    if shutil.disk_usage(vm.VM).free < 104*1024**3:
        raise ValueError('Preserve workstation storage reserve')
    memory = dict(line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())
    if int(memory['MemAvailable'].split()[0]) < 6*1024**2:
        raise ValueError('Preserve workstation memory reserve')
    folder = vm.VM/'live-tests'
    if folder.resolve() != folder:
        raise ValueError('Redirected test workspace')
    work = Path(tempfile.mkdtemp(prefix='recovery-'+args.case+'-',dir=folder))
    token = uuid.uuid4().hex; name = 'toddy-recovery-'+token[:12]
    result = {'complete':False, 'case':args.case, 'iso_sha256':manifest['media']['sha256'],
              'physical_hardware_tested':False,'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()}
    def save():
        p=work/'result.json.part';p.write_text(json.dumps(result,indent=2)+'\n');p.replace(work/'result.json')
    save(); print('RECOVERY_WORKSPACE '+str(work),flush=True)
    image = subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',vm.IMAGE],text=True).strip()
    qemu = ['qemu-system-x86_64','-enable-kvm','-machine','q35','-cpu','qemu64','-smp','2','-m','2048',
            '-display','none','-serial','unix:/work/serial.sock,server=on,wait=on','-monitor','none',
            '-nic','none','-no-reboot']
    medium = iso
    if args.case == 'corrupt':
        start,size = payload(iso, ['live','rootfs.squashfs'], manifest['compression_binding']['rootfs_sha256'])
        medium=work/'corrupted.iso';shutil.copyfile(iso,medium)
        position=start+size//2
        with medium.open('r+b') as stream:
            stream.seek(position); original=stream.read(1);stream.seek(position);stream.write(bytes([original[0]^1]))
        result['corruption']={'offset':position,'xor':1,'root_extent':[start,size],'sha256':boot.digest(medium)}
    if args.case == 'missing':
        for filename in ('vmlinuz-7.1.8-toddy','initramfs.cpio.gz'):
            values=[v for k,v in manifest['input_sha256'].items() if Path(k).name==filename]
            if len(values)!=1:raise ValueError('Ambiguous native boot input')
            payload(iso,['boot',filename],values[0],work/filename)
        qemu+=['-kernel','/work/vmlinuz-7.1.8-toddy','-initrd','/work/initramfs.cpio.gz',
               '-append','toddy.live console=ttyS0,115200n8']
    else:
        qemu+=['-drive','file=/media/toddy.iso,media=cdrom,readonly=on,format=raw','-boot','d']
    result.update(qemu_arguments=qemu,container_image=image);save()
    cid=None;connection=None;started=time.monotonic()
    try:
        cid=subprocess.check_output(['docker','create','--name',name,'--label','toddy.boot-test='+token,
            '--user',f'{os.getuid()}:{os.getgid()}','--cap-drop=ALL','--security-opt=no-new-privileges',
            '--read-only','--network=none','--device','/dev/kvm','--group-add',str(Path('/dev/kvm').stat().st_gid),
            '--memory','3g','--cpus','2','-v',f'{medium}:/media/toddy.iso:ro','-v',f'{work}:/work',image,*qemu],text=True).strip()
        result['container_id']=cid;save();subprocess.run(['docker','start',cid],check=True,stdout=subprocess.DEVNULL)
        connection=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        for attempt in range(200):
            try:connection.connect(str(work/'serial.sock'));break
            except (FileNotFoundError,ConnectionRefusedError):time.sleep(.1)
        else:raise TimeoutError('Missing guest serial socket')
        received=bytearray();selected=False;sent=False;verified=False
        marker=('TODDY_RECOVERY_OK_'+token).encode()
        with (work/'serial.log').open('xb') as log:
            while time.monotonic()-started<120:
                if select.select([connection],[],[],1)[0]:
                    data=connection.recv(65536)
                    if not data:break
                    received.extend(data);log.write(data);log.flush()
                if args.case=='rescue' and not selected and b'Toddy OS early recovery shell' in received:
                    connection.sendall(b'\x1b[B\r');selected=True
                if b'Early boot stopped.' in received and b'bash-5.3#' in received and not sent:
                    # Marker is assembled at runtime, so terminal echo cannot satisfy it.
                    command=("printf 'TODDY_RECOVERY_PID1=%s\\n' \"$(readlink /proc/1/exe)\"; "
                             "test \"$(readlink /proc/1/exe)\" = /usr/bin/bash && test ! -e /run/toddy/live-session "
                             "&& test ! -e /newroot/usr/lib/systemd/systemd "
                             "&& printf 'TODDY_RECOVERY_%s\\n' 'OK_"+token+"'\n")
                    connection.sendall(command.encode());sent=True
                if marker in received:
                    verified=True;break
        text=received.decode(errors='replace')
        expected=('Recovery requested on the kernel command line' if args.case=='rescue'
                  else 'No verified Toddy ISO filesystem found')
        if not verified or 'TODDY_LIVE_ERROR: '+expected not in text:
            raise ValueError('Expected actual recovery-shell execution did not pass')
        if args.case=='corrupt' and 'Toddy root image SHA-256 mismatch' not in text:
            raise ValueError('Corruption was not rejected by the actual digest check')
        if 'TODDY_LIVE_MEDIA_VERIFIED' in text or 'TODDY_LIVE_ROOT_READY' in text:
            raise ValueError('Unaccepted medium reached live root')
        result['container_state']=boot.stop_owned_container(cid,token)
        if boot.digest(iso)!=manifest['media']['sha256']:raise ValueError('Original ISO changed')
        result.update(complete=True,recovery_shell_executed=True,unverified_root_not_started=True,
                      original_iso_unchanged=True,elapsed_seconds=time.monotonic()-started,
                      shutdown='Owned diskless recovery-loop VM intentionally stopped after evidence; not graceful guest poweroff')
    except BaseException as error:
        result['error']=str(error)
        if cid:result['container_state']=boot.stop_owned_container(cid,token)
        raise
    finally:
        if connection:connection.close()
        if cid:
            logs=subprocess.run(['docker','logs',cid],capture_output=True)
            (work/'qemu.log').write_bytes(logs.stdout+logs.stderr)
        if (work/'serial.log').exists():result['serial_sha256']=boot.digest(work/'serial.log')
        save()


if __name__=='__main__':main()
