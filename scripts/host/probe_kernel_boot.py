#!/usr/bin/env python3
"""Boot the private native kernel with diagnostic PID 1; no foundation acceptance."""
import argparse
import base64
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
from probe_grub_media import save, run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kernel_fixture', type=Path)
    args = parser.parse_args()
    if (args.kernel_fixture.parent != Path('/mnt/lfs/sources/recovery')
            or not args.kernel_fixture.name.startswith('kernel-native-')):
        raise ValueError('Use the exact terminal private kernel fixture')
    lock = os.open(vm.VM / 'native-boot-test.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    boot.refuse_running_tests()
    memory = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
    if int(memory['MemAvailable'].split()[0]) < 4 * 1024**2:
        raise ValueError('Preserve host RAM for a separate 1 GiB diagnostic guest')
    folder = vm.VM / 'kernel-smoke-tests'
    folder.mkdir(exist_ok=True)
    if folder.resolve() != folder:
        raise ValueError('Canonical private diagnostic storage required')
    base = Path(tempfile.mkdtemp(prefix='probe-', dir=folder))
    token = uuid.uuid4().hex
    print('HOST_KERNEL_SMOKE_FIXTURE ' + str(base), flush=True)
    helper = (boot.ROOT / 'scripts/build/h09/kernel_smoke_prepare.py').read_bytes()
    init = (boot.ROOT / 'scripts/build/h09/kernel_smoke_init.c').read_bytes()
    script = '''import base64,json,subprocess
from pathlib import Path
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
namespace={'__name__':'kernel_smoke_prepare'}
exec(base64.b64decode(HELPER),namespace)
print(json.dumps(namespace['prepare'](Path(KERNEL),base64.b64decode(INIT),TOKEN)))
'''
    definitions = 'HELPER, KERNEL, INIT, TOKEN = ' + repr((base64.b64encode(helper).decode(),
        str(args.kernel_fixture), base64.b64encode(init).decode(), token)) + '\n'
    source = (definitions + script).encode()
    save(base / 'intent.json', {'kernel_fixture': str(args.kernel_fixture), 'token': token,
         'helper_sha256': hashlib.sha256(helper).hexdigest(), 'init_source_sha256': hashlib.sha256(init).hexdigest(),
         'pid': os.getpid()})
    result = {'complete': False, 'foundation_accepted': False, 'systemd_boot_verified': False,
              'release_iso': False, 'physical_hardware_tested': False, 'runs': []}
    exit_code = 1
    try:
        with (base / 'native-prepare.log').open('xb') as log:
            prepared = subprocess.run(vm.ssh_args() + ['python3 -B -'], input=source,
                                      stdout=log, stderr=subprocess.STDOUT, timeout=60)
        save(base / 'native-prepare.exit.json', {'exit': prepared.returncode})
        prepared.check_returncode()
        built = json.loads((base / 'native-prepare.log').read_text().splitlines()[-1])
        remote = Path(built['fixture'])
        if (remote.parent != Path('/mnt/lfs/sources/recovery') or not remote.name.startswith('kernel-smoke-')
                or built['token'] != token or built['files']['init.c'] != hashlib.sha256(init).hexdigest()):
            raise ValueError('Unexpected diagnostic preparation result')
        result['native_preparation'] = built
        for name in ('bzImage', 'initramfs.cpio.gz'):
            with (base / name).open('xb') as output:
                subprocess.run(vm.ssh_args() + ['cat -- ' + shlex.quote(str(remote / name))],
                               stdout=output, check=True, timeout=60)
            if boot.digest(base / name) != built['files'][name]:
                raise ValueError('Transferred diagnostic artifact differs')
        image = run('docker', 'image', 'inspect', '--format', '{{.Id}}', vm.IMAGE).stdout.strip()
        docker_base = ['--user', f'{os.getuid()}:{os.getgid()}', '--cap-drop=ALL',
                       '--security-opt=no-new-privileges', '--network=none', '--read-only']
        hashes = run('docker', 'run', '--rm', *docker_base, image,
                     'sha256sum', boot.CODE, boot.VARS).stdout
        if {line.split()[1]: line.split()[0] for line in hashes.splitlines()} != boot.FIRMWARE_HASHES:
            raise ValueError('Pinned UEFI firmware differs')
        result['container_image'] = image
        for firmware in ('bios', 'uefi'):
            work = base / firmware
            work.mkdir()
            mounts = ['-v', f'{base}/bzImage:/media/kernel:ro',
                      '-v', f'{base}/initramfs.cpio.gz:/media/initramfs:ro', '-v', f'{work}:/work']
            if firmware == 'uefi':
                run('docker', 'run', '--rm', *docker_base, *mounts, image,
                    'cp', boot.VARS, '/work/OVMF_VARS.fd')
                if boot.digest(work / 'OVMF_VARS.fd') != boot.FIRMWARE_HASHES[boot.VARS]:
                    raise ValueError('Private firmware variables differ')
            qemu = ['qemu-system-x86_64', '-enable-kvm', '-machine', 'q35', '-cpu', 'qemu64',
                    '-smp', '2', '-m', '1024', '-display', 'none', '-serial', 'file:/work/serial.log',
                    '-monitor', 'none', '-nic', 'none', '-no-reboot', '-kernel', '/media/kernel',
                    '-initrd', '/media/initramfs', '-append',
                    'console=ttyS0,115200 rdinit=/init panic=-1 toddy_probe_mode=' + firmware + ' toddy_probe_token=' + token]
            if firmware == 'uefi':
                qemu += ['-drive', f'if=pflash,format=raw,readonly=on,file={boot.CODE}',
                         '-drive', 'if=pflash,format=raw,file=/work/OVMF_VARS.fd']
            name = 'toddy-kernel-probe-' + uuid.uuid4().hex[:12]
            create = ['docker', 'create', '--name', name, '--label', 'toddy.boot-test=' + name,
                      *docker_base, *mounts, '--device', '/dev/kvm', '--group-add',
                      str(Path('/dev/kvm').stat().st_gid), '--memory', '2g', '--cpus', '2', image, *qemu]
            save(work / 'intent.json', {'argv': create, 'timeout_seconds': 60})
            cid = run(*create).stdout.strip()
            save(work / 'container.json', {'id': cid, 'name': name})
            try:
                run('docker', 'start', cid)
                wait = run('docker', 'wait', cid, timeout=60)
                state = json.loads(run('docker', 'inspect', cid).stdout)[0]['State']
                save(work / 'exit.json', state)
                if wait.stdout.strip() != '0' or state['ExitCode'] != 0 or state['OOMKilled']:
                    raise ValueError('Private kernel guest failed')
                serial = (work / 'serial.log').read_text(errors='replace')
                sentinel = 'TODDY_KERNEL_SMOKE_OK token=' + token + ' firmware=' + firmware
                if (serial.splitlines().count(sentinel) != 1 or 'TODDY_KERNEL_SMOKE_FAIL' in serial
                        or 'Kernel panic' in serial):
                    raise ValueError('Missing or failed native kernel assertions')
                result['runs'].append({'firmware': firmware, 'exit': 0, 'kernel_boot_verified': True,
                    'native_module_insert_remove': True, 'namespaces_created': True,
                    'volatile_data_roundtrip': True, 'serial_sha256': boot.digest(work / 'serial.log')})
                print('KERNEL_SMOKE_PASSED ' + firmware, flush=True)
            finally:
                terminal = boot.stop_owned_container(cid, name)
                save(work / 'terminal.json', terminal)
                if not terminal['Running']:
                    run('docker', 'rm', cid)
        for name in ('bzImage', 'initramfs.cpio.gz'):
            if boot.digest(base / name) != built['files'][name]:
                raise ValueError('Diagnostic media changed during boot')
        result['complete'] = True
        exit_code = 0
    except BaseException as error:
        result['error'] = str(error)
        raise
    finally:
        save(base / 'result.json', result)
        save(base / 'driver.exit.json', {'exit': exit_code})
        print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
