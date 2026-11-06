#!/usr/bin/env python3
"""Run H09 BIOS/UEFI checks on a private overlay of a verified cold checkpoint."""
import argparse
import base64
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
import uuid

import vm

ROOT = Path(__file__).resolve().parents[2]
CODE = '/usr/share/OVMF/OVMF_CODE_4M.fd'
VARS = '/usr/share/OVMF/OVMF_VARS_4M.fd'
FIRMWARE_HASHES = {
    CODE: 'ad23261d43116abc3747d59a7837fbf578c9586a8993f4eeba064cd07eccb083',
    VARS: '5d2ac383371b408398accee7ec27c8c09ea5b74a0de0ceea6513388b15be5d1e',
}
PAYLOADS = {
    'systemd.extra-unit.toddy-boot-probe.service': 'boot-probe.service',
    'systemd.unit-dropin.multi-user.target': 'boot-probe.target.conf',
    'toddy.boot-probe': 'boot-probe.py',
}


def run(*command, **kwargs):
    return subprocess.run(command, check=True, text=True, **kwargs)


def digest(path):
    before = path.stat()
    with path.open('rb') as stream:
        result = hashlib.file_digest(stream, 'sha256').hexdigest()
    after = path.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError('Checkpoint changed while hashing')
    return result


def read_checkpoint(folder, name):
    if not re.fullmatch(r'h09-[a-z0-9][a-z0-9-]{0,34}', name):
        raise ValueError('Use a named H09 cold checkpoint')
    if folder.is_symlink() or folder.resolve() != folder:
        raise ValueError('Checkpoint directory must be canonical, with no symlink ancestors')
    manifest = folder / (name + '.json')
    if manifest.is_symlink() or not manifest.is_file():
        raise ValueError('Checkpoint manifest must be a regular file')
    data = json.loads(manifest.read_text())
    if data.get('name') != name or set(data.get('disks', {})) != {'builder', 'target'}:
        raise ValueError('Expected a paired cold checkpoint manifest')
    for role in ('builder', 'target'):
        entry = data['disks'][role]
        if entry.get('file') != f'{name}-{role}.qcow2':
            raise ValueError('Unexpected checkpoint disk filename')
        if not re.fullmatch(r'[0-9a-f]{64}', entry.get('sha256', '')):
            raise ValueError('Missing checkpoint SHA-256')
        path = folder / entry['file']
        if path.is_symlink() or not path.is_file():
            raise ValueError('Checkpoint disk must be a regular file')
    return data, folder / data['disks']['target']['file']


def qemu_arguments(firmware, payloads):
    if firmware not in {'bios', 'uefi'}:
        raise ValueError('Unsupported firmware mode')
    arguments = ['qemu-system-x86_64', '-enable-kvm', '-machine', 'q35',
                 '-cpu', 'qemu64', '-smp', '2', '-m', '2048', '-display', 'none',
                 '-serial', 'file:/work/serial.log', '-monitor', 'none',
                 '-nic', 'none', '-no-reboot', '-boot', 'strict=on',
                 '-object', 'rng-random,id=rng0,filename=/dev/urandom',
                 '-device', 'virtio-rng-pci,rng=rng0',
                 '-drive', 'file=/work/target.qcow2,if=none,id=root,format=qcow2',
                 '-device', 'virtio-blk-pci,drive=root,serial=TODDY-BOOT-TEST']
    if firmware == 'uefi':
        arguments += ['-drive', f'if=pflash,format=raw,readonly=on,file={CODE}',
                      '-drive', 'if=pflash,format=raw,file=/work/OVMF_VARS.fd']
    if set(payloads) != set(PAYLOADS):
        raise ValueError('Expected only the three versioned public test payloads')
    for name, contents in sorted(payloads.items()):
        encoded = base64.b64encode(contents).decode('ascii')
        if len(encoded) > 16384:
            raise ValueError('Unexpectedly large SMBIOS test payload')
        arguments += ['-smbios', f'type=11,value=io.systemd.credential.binary:{name}={encoded}']
    return arguments


def parse_report(serial, firmware):
    if 'TODDY_NATIVE_BOOT_FAIL ' in serial:
        raise ValueError('Native boot probe reported failure')
    reports = [json.loads(line.split('TODDY_NATIVE_BOOT_OK ', 1)[1])
               for line in serial.splitlines() if 'TODDY_NATIVE_BOOT_OK ' in line]
    if not reports or any(report != reports[0] for report in reports):
        raise ValueError('Missing or inconsistent native boot report')
    report = reports[0]
    if report.get('firmware') != firmware or report.get('kernel') != '7.1.8-toddy':
        raise ValueError('Wrong firmware mode or native kernel')
    if report.get('pid1') != 'systemd' or report.get('virtualization') not in {'kvm', 'qemu'}:
        raise ValueError('Wrong native execution environment')
    if any(report.get(key) is not True for key in ('native_c_execution', 'dummy_load_unload')):
        raise ValueError('Native execution/module checks did not pass')
    linkage = report.get('native_linkage', '')
    if '/lib64/ld-linux-x86-64.so.2' not in linkage or '/tools/' in linkage or '/sources/' in linkage:
        raise ValueError('Missing native linkage or temporary paths in report')
    if not re.fullmatch(r'/dev/[a-z0-9]+', report.get('root_source', '')):
        raise ValueError('Missing native root device')
    return report


def stop_owned_container(cid, run_id):
    inspection = json.loads(subprocess.check_output(['docker', 'inspect', cid], text=True))[0]
    if (inspection['Config'].get('Labels') or {}).get('toddy.boot-test') != run_id:
        raise ValueError('Refusing to stop a container with a different test identity')
    if inspection['State']['Running']:
        run('docker', 'stop', '--time', '10', cid, stdout=subprocess.DEVNULL)
    state = json.loads(subprocess.check_output(['docker', 'inspect', cid], text=True))[0]['State']
    if state['Running']:
        raise ValueError('Test container remains running')
    return state


def refuse_running_tests():
    running = subprocess.check_output(['docker', 'ps', '-q', '--filter', 'label=toddy.boot-test'], text=True).strip()
    if running:
        raise ValueError('A native boot test is still running; inspect its existing handle instead of restarting')


def prerequisites():
    states = {item['id']: item['status'] for item in json.loads((ROOT / 'status.json').read_text())['milestones']}
    if states['H08'] != 'completed' or states['H09'] != 'in_progress':
        raise ValueError('Native boot tests require H08 completed and H09 in_progress')
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip():
        raise ValueError('Commit reviewed inputs before native boot testing')
    source = '''from pathlib import Path
import json,subprocess
subprocess.run(['python3','/opt/toddy-build/scripts/build/h09/require_gate.py'],check=True)
records={}
for step in ('kernel','boot-config','bootloader'):
 record=json.loads((Path('/var/log/toddy/build')/('h09-'+step+'.success.json')).read_text())
 assert record['recipe_exit']==0 and record['postcheck_exit']==0,(step,record)
 records[step]=record
print(json.dumps(records))
'''
    output = subprocess.check_output(vm.ssh_args() + ['python3 -c ' + shlex.quote(source)], text=True)
    return json.loads(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('firmware', choices=['bios', 'uefi'])
    parser.add_argument('--checkpoint', required=True)
    parser.add_argument('--timeout', type=int, default=300)
    args = parser.parse_args()
    if not 60 <= args.timeout <= 900:
        raise ValueError('Boot timeout must be between 60 and 900 seconds')
    accepted = prerequisites()
    checkpoint, source = read_checkpoint(vm.VM / 'checkpoints', args.checkpoint)
    lock = os.open(vm.VM / 'native-boot-test.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    # Hold this descriptor until process exit; a crash releases the flock, while
    # the Docker check also catches a guest surviving its original controller.
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    refuse_running_tests()
    created = datetime.fromisoformat(checkpoint['created_utc'])
    if any(created < datetime.fromisoformat(record['finished']) for record in accepted.values()):
        raise ValueError('Checkpoint predates accepted kernel/bootloader artifacts')
    expected = checkpoint['disks']['target']['sha256']
    if digest(source) != expected:
        raise ValueError('Cold target checksum mismatch')
    if shutil.disk_usage(vm.VM).free < 104 * 1024**3:
        raise ValueError('Preserve 100 GiB host reserve plus test workspace allowance')
    memory = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
    if int(memory['MemAvailable'].split()[0]) < 6 * 1024**2:
        raise ValueError('Need 6 GiB available RAM for guest plus host reserve')
    folder = vm.VM / 'boot-tests'
    if folder.is_symlink() or folder.resolve() != folder:
        raise ValueError('Boot test directory must be canonical')
    folder.mkdir(exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix='h09-' + args.firmware + '-', dir=folder))
    if any(':' in str(path) for path in (source, work)):
        raise ValueError('Docker bind paths cannot contain a colon')
    run_id = uuid.uuid4().hex
    name = 'toddy-boot-' + run_id[:16]
    image = subprocess.check_output(['docker', 'image', 'inspect', '--format', '{{.Id}}', vm.IMAGE], text=True).strip()
    docker_base = ['--user', f'{os.getuid()}:{os.getgid()}', '--cap-drop=ALL',
                   '--security-opt=no-new-privileges', '--network=none', '--read-only',
                   '-v', f'{source}:/checkpoint/target.qcow2:ro', '-v', f'{work}:/work']
    state = {'run_id': run_id, 'container_name': name, 'container_image': image,
             'firmware': args.firmware, 'checkpoint': checkpoint['name'],
             'checkpoint_target_sha256': expected, 'accepted_artifacts': accepted,
             'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
             'milestone_accepted': False, 'phase': 'preparing'}

    def save():
        state['updated_at'] = datetime.now(timezone.utc).isoformat()
        temporary = work / 'result.json.part'
        temporary.write_text(json.dumps(state, indent=2) + '\n')
        temporary.replace(work / 'result.json')
        print(json.dumps({'phase': state['phase'], 'workspace': str(work), 'container': name}), flush=True)

    cid = None
    save()
    try:
        with (work / 'prepare.log').open('w') as log:
            run('docker', 'run', '--rm', *docker_base, image, 'qemu-img', 'check',
                '/checkpoint/target.qcow2', stdout=log, stderr=subprocess.STDOUT)
            info = json.loads(subprocess.check_output(['docker', 'run', '--rm', *docker_base, image,
                               'qemu-img', 'info', '--output=json', '/checkpoint/target.qcow2'], text=True))
            if info.get('format') != 'qcow2' or info.get('backing-filename') or info['virtual-size'] != 180 * 1024**3:
                raise ValueError('Expected the standalone 180 GiB designated target checkpoint')
            run('docker', 'run', '--rm', *docker_base, image, 'qemu-img', 'create',
                '-f', 'qcow2', '-F', 'qcow2', '-b', '/checkpoint/target.qcow2',
                '/work/target.qcow2', stdout=log, stderr=subprocess.STDOUT)
            if args.firmware == 'uefi':
                actual = subprocess.check_output(['docker', 'run', '--rm', *docker_base, image,
                           'sha256sum', CODE, VARS], text=True)
                if {line.split()[1]: line.split()[0] for line in actual.splitlines()} != FIRMWARE_HASHES:
                    raise ValueError('UEFI infrastructure changed; review its new inputs first')
                state['firmware_sha256'] = FIRMWARE_HASHES
                run('docker', 'run', '--rm', *docker_base, image, 'cp', VARS, '/work/OVMF_VARS.fd',
                    stdout=log, stderr=subprocess.STDOUT)
                if digest(work / 'OVMF_VARS.fd') != FIRMWARE_HASHES[VARS]:
                    raise ValueError('Private UEFI variable template differs')
        payloads = {key: (ROOT / 'scripts/host' / filename).read_bytes() for key, filename in PAYLOADS.items()}
        state['payload_sha256'] = {key: hashlib.sha256(value).hexdigest() for key, value in payloads.items()}
        command = ['docker', 'create', '--name', name, '--label', 'toddy.boot-test=' + run_id,
                   *docker_base, '--device', '/dev/kvm', '--group-add', str(Path('/dev/kvm').stat().st_gid),
                   '--memory', '3g', '--cpus', '2', image, *qemu_arguments(args.firmware, payloads)]
        cid = subprocess.check_output(command, text=True).strip()
        state.update(container_id=cid, phase='running')
        save()
        with (work / 'qemu.log').open('w') as log:
            result = subprocess.run(['docker', 'start', '--attach', cid], stdout=log,
                                    stderr=subprocess.STDOUT, timeout=args.timeout)
        state['attach_exit'] = result.returncode
        result.check_returncode()
        inspection = json.loads(subprocess.check_output(['docker', 'inspect', cid], text=True))[0]
        state['container_state'] = inspection['State']
        if inspection['State']['Running'] or inspection['State']['ExitCode'] != 0:
            raise ValueError('QEMU did not exit cleanly')
        state['native_report'] = parse_report((work / 'serial.log').read_text(errors='replace'), args.firmware)
        if digest(source) != expected:
            raise ValueError('Cold backing checkpoint changed during boot test')
        state.update(phase='passed', checkpoint_unchanged=True)
        save()
    except BaseException as error:
        state.update(phase='failed', error=str(error))
        if cid:
            try:
                state['container_state'] = stop_owned_container(cid, run_id)
            except Exception as cleanup_error:
                state.update(phase='cleanup_uncertain', cleanup_error=str(cleanup_error))
        save()
        raise


if __name__ == '__main__':
    main()
