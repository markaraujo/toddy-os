#!/usr/bin/env python3
"""Build and boot a loader-only native ISO; no kernel or foundation acceptance."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import uuid

import boot_test as boot
import vm


def save(path, value):
    with path.open('x') as stream:
        stream.write(json.dumps(value, indent=2) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def run(*command, **kwargs):
    return subprocess.run(command, check=True, text=True, capture_output=True, **kwargs)


def collect_native(remote, built):
    script = 'BASE=' + repr(str(remote)) + '\n' + '''from pathlib import Path
import hashlib,json
base=Path(BASE)
assert base.resolve()==base and base.parent==Path('/mnt/lfs/sources/recovery') and base.name.startswith('grub-media-')
files={p.name:p.read_text() for p in base.iterdir() if p.is_file() and p.suffix in ('.json','.log')}
print(json.dumps({'fixture':str(base),'files':files,'sha256':{name:hashlib.sha256(body.encode()).hexdigest() for name,body in files.items()}},indent=2))
'''
    report = json.loads(run(*vm.ssh_args(), 'python3 -B -', input=script, timeout=30).stdout)
    if json.loads(report['files']['result.json']) != built:
        raise ValueError('Collected native result differs')
    for stage in built['stages']:
        if (report['sha256'][stage['name'] + '.log'] != stage['log_sha256']
                or json.loads(report['files'][stage['name'] + '.exit.json']) != {'exit': 0}):
            raise ValueError('Collected stage log or exit differs')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mtools_fixture')
    parser.add_argument('libburnia_fixture')
    args = parser.parse_args()
    for value, prefix in ((args.mtools_fixture, 'mtools-native-'),
                          (args.libburnia_fixture, 'libburnia-native-')):
        path = Path(value)
        if path.parent != Path('/mnt/lfs/sources/recovery') or not path.name.startswith(prefix):
            raise ValueError('Use exact completed private native fixtures')
    lock = os.open(vm.VM / 'native-boot-test.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    boot.refuse_running_tests()
    memory = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
    if int(memory['MemAvailable'].split()[0]) < 3 * 1024**2:
        raise ValueError('Preserve 3 GiB host RAM availability before this 512 MiB guest')
    folder = vm.VM / 'grub-media-tests'
    folder.mkdir(exist_ok=True)
    if folder.resolve() != folder:
        raise ValueError('Private test storage must be canonical')
    base = Path(tempfile.mkdtemp(prefix='probe-', dir=folder))
    print('HOST_GRUB_MEDIA_FIXTURE ' + str(base), flush=True)
    source = (boot.ROOT / 'scripts/build/h11/grub_media_probe.py').read_bytes()
    (base / 'native-build.py').write_bytes(source)
    save(base / 'intent.json', {'pid': os.getpid(), 'mtools': args.mtools_fixture,
         'libburnia': args.libburnia_fixture, 'source_sha256': hashlib.sha256(source).hexdigest()})
    result = {'release_iso': False, 'kernel_boot_verified': False,
              'milestone_accepted': False, 'physical_hardware_tested': False, 'runs': []}
    exit_code = 1
    try:
        with (base / 'native-build.log').open('x') as log:
            build = subprocess.run(vm.ssh_args() + ['python3 -B - ' + shlex.join(
                [args.mtools_fixture, args.libburnia_fixture])], input=source,
                stdout=log, stderr=subprocess.STDOUT, timeout=150)
            log.flush()
            os.fsync(log.fileno())
        save(base / 'native-build.exit.json', {'exit': build.returncode})
        build.check_returncode()
        built = json.loads((base / 'native-build.log').read_text().splitlines()[-1])
        if not built.get('complete'):
            raise ValueError('Native media assembly failed')
        remote = Path(built['fixture'])
        if remote.parent != Path('/mnt/lfs/sources/recovery') or not remote.name.startswith('grub-media-'):
            raise ValueError('Unexpected remote media path')
        save(base / 'native-evidence.json', collect_native(remote, built))
        iso = base / 'loader-probe.iso'
        with iso.open('xb') as output:
            subprocess.run(vm.ssh_args() + ['cat -- ' + shlex.quote(str(remote / iso.name))],
                           stdout=output, check=True, timeout=60)
        if boot.digest(iso) != built['iso_sha256'] or iso.stat().st_size != built['iso_size']:
            raise ValueError('Transferred image checksum differs')
        result['native_assembly'] = built
        image = run('docker', 'image', 'inspect', '--format', '{{.Id}}', vm.IMAGE).stdout.strip()
        docker_base = ['--user', f'{os.getuid()}:{os.getgid()}', '--cap-drop=ALL',
                       '--security-opt=no-new-privileges', '--network=none', '--read-only']
        hashes = run('docker', 'run', '--rm', *docker_base, image,
                     'sha256sum', boot.CODE, boot.VARS).stdout
        if {line.split()[1]: line.split()[0] for line in hashes.splitlines()} != boot.FIRMWARE_HASHES:
            raise ValueError('UEFI firmware differs from the pinned H09 baseline')
        result['container_image'] = image
        result['firmware_sha256'] = boot.FIRMWARE_HASHES
        for firmware, medium in (('bios', 'cdrom'), ('uefi', 'cdrom'),
                                 ('bios', 'usb'), ('uefi', 'usb')):
            work = base / (firmware + '-' + medium)
            work.mkdir()
            mounts = ['-v', f'{iso}:/media/loader.iso:ro', '-v', f'{work}:/work']
            if firmware == 'uefi':
                run('docker', 'run', '--rm', *docker_base, *mounts, image,
                    'cp', boot.VARS, '/work/OVMF_VARS.fd')
                if boot.digest(work / 'OVMF_VARS.fd') != boot.FIRMWARE_HASHES[boot.VARS]:
                    raise ValueError('Private firmware-variable template differs')
            qemu = ['qemu-system-x86_64', '-enable-kvm', '-machine', 'q35', '-cpu', 'qemu64',
                    '-smp', '1', '-m', '512', '-display', 'none', '-serial', 'file:/work/serial.log',
                    '-monitor', 'none', '-nic', 'none', '-no-reboot']
            if medium == 'cdrom':
                qemu += ['-drive', 'file=/media/loader.iso,media=cdrom,format=raw,readonly=on',
                         '-boot', 'order=d,strict=on']
            else:
                qemu += ['-device', 'qemu-xhci,id=xhci', '-drive',
                         'file=/media/loader.iso,if=none,id=media,format=raw,readonly=on',
                         '-device', 'usb-storage,bus=xhci.0,drive=media', '-boot', 'order=c,strict=on']
            if firmware == 'uefi':
                qemu += ['-drive', f'if=pflash,format=raw,readonly=on,file={boot.CODE}',
                         '-drive', 'if=pflash,format=raw,file=/work/OVMF_VARS.fd']
            name = 'toddy-grub-probe-' + uuid.uuid4().hex[:12]
            create = ['docker', 'create', '--name', name, '--label', 'toddy.boot-test=' + name,
                      *docker_base, *mounts, '--device', '/dev/kvm', '--group-add',
                      str(Path('/dev/kvm').stat().st_gid), '--memory', '1g', '--cpus', '1', image, *qemu]
            save(work / 'intent.json', {'argv': create, 'timeout_seconds': 45})
            cid = run(*create).stdout.strip()
            save(work / 'container.json', {'id': cid, 'name': name})
            try:
                run('docker', 'start', cid)
                wait = run('docker', 'wait', cid, timeout=45)
                state = json.loads(run('docker', 'inspect', cid).stdout)[0]['State']
                save(work / 'exit.json', state)
                if wait.stdout.strip() != '0' or state['ExitCode'] != 0 or state['OOMKilled']:
                    raise ValueError('Loader guest failed or was killed')
                serial = (work / 'serial.log').read_text(errors='replace')
                platform = 'pc' if firmware == 'bios' else 'efi'
                if (serial.count('TODDY_GRUB_MEDIA_EXEC platform=' + platform + ' token=' + built['token']) != 1
                        or serial.count('TODDY_GRUB_MEDIA_DATA ' + built['token']) != 1
                        or 'error:' in serial.lower()):
                    raise ValueError('Missing, duplicate or failed actual loader execution/readback')
                result['runs'].append({'firmware': firmware, 'medium': medium, 'exit': 0,
                    'serial_sha256': boot.digest(work / 'serial.log'), 'loader_executed': True,
                    'iso_data_read': True, 'kernel_boot_verified': False})
                print('GRUB_MEDIA_PASSED ' + firmware + ' ' + medium, flush=True)
            finally:
                logs = run('docker', 'logs', cid)
                (work / 'qemu.log').write_text(logs.stdout + logs.stderr)
                state = boot.stop_owned_container(cid, name)
                save(work / 'final-container-state.json', state)
                run('docker', 'rm', cid)
        if boot.digest(iso) != built['iso_sha256']:
            raise ValueError('Read-only boot media changed')
        result.update(complete=True, media_unchanged=True)
        exit_code = 0
    except BaseException as error:
        result.update(complete=False, error=str(error))
        raise
    finally:
        save(base / 'result.json', result)
        save(base / 'driver.exit.json', {'exit': exit_code})
        print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
