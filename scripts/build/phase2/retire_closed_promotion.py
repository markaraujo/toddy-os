"""Reclaim an explicitly qualified closed promotion copy, preserving recovery."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from retire_llvm_stages import digest, verify_package_stage
from run_step import snapshot
from verify_stage import inspect_stage

PROFILES = {
    'gstreamer': {
        'name': 'gstreamer',
        'version': '1.28.6-1+toddy1',
        'native_step': 'b02-gstreamer-install',
        'native_receipt': '547e3080ab4128f7ebae1c3d48cabb9e7bb102e99ca31d59983c751d66de9c29',
        'record': '76f7bcf0ec9c85faed87fae20cf8a1d12ec726b586599f184da7cba121904c0d',
        'archive': 'e51ed504763515f4f607255d2f77d588bcf8820e8608f1590153418d4fcef9e0',
        'work_manifest': '6bf1e1f6a861cd2d320c73caf9e30c9b2d0856c4dee91628008e0b7fb5f6b9b7',
        'stage_inode': 7418960,
    },
    'qtbase-probe': {
        'name': 'qtbase',
        'version': '6.11.2-1+toddy1',
        'native_step': 'b01-qtbase-probe-package',
        'native_receipt': '5649f7a0dc95fdffc37ba8ae10ce875b2b87b61d6c9c804f3d7ec39000c12f22',
        'record': '1efacbb32ad711f11060f4eb89f8f2798e567486457e5f6884ff5074e9459245',
        'archive': '03a7deaeaca8fa66c65a0fcc67330e9f0fbf52f738e99767577cb29b43b927fa',
        'work_manifest': '12e8e9f507781fc42b0206b9ea57520fb3fccf95f5bff287b31d4d0b8cb056e6',
        'stage_inode': 10941206,
    },
}


def free_bytes(target):
    space = os.statvfs(target)
    return space.f_bavail * space.f_frsize


def retain_bytes(root):
    return {str(path.relative_to(root)): digest(path) for path in root.rglob('*')
            if path.is_file() and not path.is_symlink()}


def retire(profile):
    spec = PROFILES[profile]
    subprocess.run(['bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    target = Path('/mnt/lfs')
    log = Path('/var/log/toddy')
    build = log / 'build'
    with (build / 'build.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert not list(build.glob('*.running.json')) and not (build / 'input-sync.running').exists()
        receipt = log / 'phase2' / f'{profile}-promotion-custody-1.json'
        part = receipt.with_suffix('.part')
        assert not receipt.exists() and not part.exists(), 'Reconcile prior custody before mutation'
        native_receipt = build / (spec['native_step'] + '.success.json')
        assert digest(native_receipt) == spec['native_receipt']
        native = json.loads(native_receipt.read_text())
        assert native['recipe_exit'] == native['postcheck_exit'] == 0
        basename = f"{spec['name']}_{spec['version']}_amd64"
        record_path = log / 'packages' / (basename + '.json')
        archive = Path('/var/cache/toddy/packages') / (basename + '.deb')
        assert digest(record_path) == spec['record']
        record = json.loads(record_path.read_text())
        assert record['installed'] and not record['generated_paths']
        assert archive.is_file() and not archive.is_symlink()
        assert digest(archive) == record['archive_sha256'] == spec['archive']
        status = subprocess.check_output(['chroot', str(target), 'dpkg-query', '-W',
                                          '-f=${Status} ${Version}', spec['name']], text=True)
        assert status == 'install ok installed ' + spec['version']

        stage = target / 'sources/stage' / ('phase2-' + profile)
        original = target / 'sources/phase2/work' / (profile + '-1') / 'stage'
        assert stage.resolve() == stage and stage.stat().st_ino == spec['stage_inode']
        assert stage.stat().st_dev == target.stat().st_dev and not (stage / 'usr').is_symlink()
        mounts = subprocess.check_output(['findmnt', '-rn', '-o', 'TARGET'], text=True).splitlines()
        assert not any(Path(path).is_relative_to(stage) for path in mounts)
        verify_package_stage(stage, record['payload'])
        for relative, row in record['payload'].items():
            installed = target / relative.lstrip('/')
            if 'sha256' in row:
                assert installed.is_file() and not installed.is_symlink() and digest(installed) == row['sha256']
            if 'symlink' in row:
                assert installed.is_symlink() and os.readlink(installed) == row['symlink']
        original_manifest = inspect_stage(original)
        assert original_manifest['manifest_sha256'] == spec['work_manifest']
        control = retain_bytes(stage / 'DEBIAN')
        assert control

        before = snapshot()
        state = {'state': 'verified', 'stage': str(stage), 'stage_inode': spec['stage_inode'],
                 'archive_sha256': spec['archive'], 'record_sha256': spec['record'],
                 'workstage_manifest_sha256': spec['work_manifest'],
                 'before_free_bytes': free_bytes(target),
                 'scope': 'Closed promotion usr copy only. Installed root, source, compiler, original workstage, archive and control retained.'}

        def save():
            with part.open('x') as stream:
                stream.write(json.dumps(state, indent=2) + '\n')
                stream.flush()
                os.fsync(stream.fileno())
            part.replace(receipt)

        save()
        state['state'] = 'retiring'
        save()
        shutil.rmtree(stage / 'usr')
        (stage / '.toddy-retired.json').write_text(json.dumps({
            'receipt': str(receipt), 'archive': str(archive), 'archive_sha256': spec['archive']}) + '\n')
        assert retain_bytes(stage / 'DEBIAN') == control
        assert inspect_stage(original) == original_manifest
        assert digest(archive) == spec['archive'] and snapshot() == before
        state.update(state='complete', installed_root_changed_paths=0,
                     after_free_bytes=free_bytes(target),
                     recovery='Verify the retained native archive and record, then extract into a new stage. Never replay custody.')
        state['reclaimed_bytes'] = state['after_free_bytes'] - state['before_free_bytes']
        save()
        print(json.dumps(state))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('profile', choices=PROFILES)
    retire(parser.parse_args().profile)
