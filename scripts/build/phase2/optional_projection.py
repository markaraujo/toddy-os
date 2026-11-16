"""Read-only exact seven-package optional archive projection; no offline inclusion."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]
import image_projection as projection
import voice_process_reconcile as bridge
import voice_catalog_provenance as catalog_provenance

NAMES = frozenset(('toddy-voice', 'whisper-cpp', 'espeak-ng', 'pipewire-audio-tools',
    'toddy-voice-model-base', 'toddy-voice-native-catalog', 'toddy-integrations'))
OUTPUT = bridge.T / 'sources/stage/toddy-optional-projection-1'


def document(components, inventory):
    if set(components) != NAMES or any(row['name'] != name for name, row in components.items()):
        raise ValueError('Exact seven optional native packages required')
    return {'schema_version': 1,
        'scope': 'Actual optional native archives only; unsigned acquisition input, not runtime/GUI/release acceptance',
        'observed_inventory_sha256': hashlib.sha256(inventory.encode()).hexdigest(),
        'offline_base': False, 'iso_inclusion': False, 'available': False,
        'explicit_owner_acquisition_required': True,
        'components': [components[name] for name in sorted(NAMES)]}


def main():
    if sys.argv[1:] or os.getuid() != 0 or os.geteuid() != 0 or Path(__file__).resolve() != bridge.R / 'scripts/build/phase2/optional_projection.py':
        raise ValueError('Fixed designated-builder read-only coordinator command')
    subprocess.run(['/bin/bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    os.umask(0o077)
    with bridge.frozen.BUILD_LOCK.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if list(bridge.frozen.BUILD_LOCK.parent.glob('*.running.json')) or (bridge.frozen.BUILD_LOCK.parent / 'input-sync.running').exists():
            raise ValueError('Preserve active native operation')
        if os.path.lexists(OUTPUT):
            raise ValueError('Preserve prior optional projection generation')
        parent = OUTPUT.parent
        info = parent.lstat()
        if parent.resolve() != parent or info.st_uid or info.st_gid or info.st_mode & 0o022 or info.st_dev != bridge.T.stat().st_dev:
            raise ValueError('Private same-target stage parent required')
        command = ['/usr/sbin/chroot', str(bridge.T), '/usr/bin/dpkg-query', '-W',
            '-f=${binary:Package}\t${Version}\t${Architecture}\t${Status}\t${Depends}\t${Pre-Depends}\n']
        inventory = subprocess.check_output(command, text=True, timeout=60)
        rows = projection.installed_rows(inventory)
        if not NAMES <= rows.keys():
            raise ValueError('Every optional native package must actually be installed')
        # Native voice/proof package checks are strict through catalog provenance;
        # every archive, native control, payload and legal file is verified by collect.
        components = projection.collect(NAMES, rows)
        if subprocess.check_output(command, text=True, timeout=60) != inventory:
            raise ValueError('Native inventory changed during optional projection')
        value = document(components, inventory)
        value['source_pins'] = {name: bridge.digest(HERE / name) for name in
            ('optional_projection.py', 'voice_catalog_provenance.py', 'image_projection.py',
             'voice_process_reconcile.py', 'voice_native.py')}
        value['native_catalog_package_check_sha256'] = bridge.digest(bridge.file('catalog-package-checked.json'))
        catalog_path, catalog_record = bridge.frozen.native_record(bridge.PACKAGE)
        attestation = projection.payload.encoded(catalog_provenance.export_attestation(components[bridge.PACKAGE], catalog_record))
        value['generated_catalog_attestation_sha256'] = hashlib.sha256(attestation).hexdigest()
        projection.save_generation(OUTPUT, {'optional-projection.json':
            projection.payload.encoded(value), 'generated-catalog-attestation.json': attestation})
    print(json.dumps({'state': 'optional-archive-backed-projection', 'output': str(OUTPUT),
        'available': False, 'offline_base': False, 'iso_inclusion': False}, sort_keys=True))


if __name__ == '__main__':
    main()
