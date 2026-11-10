"""Retire only the exact closed Evolution Data Server promotion replica for native headroom."""
from pathlib import Path
import fcntl
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_step import snapshot
from verify_stage import inspect_stage
from retire_llvm_stages import digest, verify_package_stage


def files(base):
    return {str(p.relative_to(base)): digest(p) for p in base.rglob('*') if p.is_file() and not p.is_symlink()}


def main():
    assert os.geteuid() == 0
    subprocess.run(['bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    build = Path('/var/log/toddy/build')
    lock = (build / 'build.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert not list(build.glob('*.running.json')) and not (build / 'input-sync.running').exists()
    receipt = Path('/var/log/toddy/phase2/eds-promotion-custody-1.json')
    assert not receipt.exists() and not receipt.with_suffix('.part').exists(), 'Reconcile actual state; never replay'
    native_receipt = build / 'b02-evolution-data-server-install.success.json'
    assert digest(native_receipt) == 'cfa4c47c828e47d472545b05eb7ce43b41e6a247d4980e965493a4be3fadbd9a'
    native = json.loads(native_receipt.read_text())
    assert native['recipe_exit'] == native['postcheck_exit'] == 0
    record_path = Path('/var/log/toddy/packages/evolution-data-server_3.60.2-1+toddy1_amd64.json')
    assert digest(record_path) == 'dbfa00874333e427ec703f11d5d93c758d6bbeef8c61ac54b69fa873fa8bab82'
    record = json.loads(record_path.read_text())
    assert record['installed'] and not record['generated_paths']
    archive = Path('/var/cache/toddy/packages/evolution-data-server_3.60.2-1+toddy1_amd64.deb')
    archive_sha = '20acb49e8aec44d53097fe51392d1f8c95d441848081dee00e3bb4f70cb866d1'
    assert not archive.is_symlink() and digest(archive) == record['archive_sha256'] == archive_sha
    target = Path('/mnt/lfs')
    assert subprocess.check_output(['chroot', str(target), 'dpkg-query', '-W', '-f=${Status} ${Version}', 'evolution-data-server'], text=True) == 'install ok installed 3.60.2-1+toddy1'
    stage = target / 'sources/stage/phase2-evolution-data-server'
    assert stage.resolve() == stage and stage.stat().st_ino == 8204877
    assert stage.stat().st_dev == target.stat().st_dev and not (stage / 'usr').is_symlink()
    verify_package_stage(stage, record['payload'])
    for relative, row in record['payload'].items():
        installed = target / relative.lstrip('/')
        if 'sha256' in row:
            assert digest(installed) == row['sha256']
        if 'symlink' in row:
            assert os.readlink(installed) == row['symlink']
    mounts = [Path(p) for p in subprocess.check_output(['findmnt', '-rn', '-o', 'TARGET'], text=True).splitlines()]
    assert not any(p == stage or p.is_relative_to(stage) for p in mounts)
    workstage = target / 'sources/phase2/work/evolution-data-server-1/stage'
    assert workstage.is_dir() and workstage.resolve() == workstage
    original = inspect_stage(workstage)
    assert original['manifest_sha256'] == 'faf24f845cf940678c9cf2f1a84d47ada1121931ff6a3f394485f5cf3741cbec'
    control = files(stage / 'DEBIAN')
    assert control
    before = snapshot()
    free_before = shutil.disk_usage(target).free
    state = {'state': 'verified', 'stage': str(stage), 'stage_inode': stage.stat().st_ino,
             'archive_sha256': archive_sha, 'record_sha256': digest(record_path),
             'workstage_manifest_sha256': original['manifest_sha256'], 'before_free_bytes': free_before,
             'scope': 'Only closed Evolution Data Server promotion usr replica; original compiler/source/workstage/archives/DEBIAN and installed payload retained'}

    def save():
        part = receipt.with_suffix('.part')
        assert not part.exists()
        with part.open('x') as stream:
            stream.write(json.dumps(state, indent=2) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        part.replace(receipt)

    save()
    state['state'] = 'retiring'
    save()
    shutil.rmtree(stage / 'usr')
    (stage / '.toddy-retired.json').write_text(json.dumps({'receipt': str(receipt), 'archive': str(archive), 'archive_sha256': archive_sha}, indent=2) + '\n')
    assert files(stage / 'DEBIAN') == control and inspect_stage(workstage) == original
    assert digest(archive) == archive_sha and snapshot() == before
    state.update(state='complete', installed_root_changed_paths=0, after_free_bytes=shutil.disk_usage(target).free,
                 recovery='Verify retained archive/record then extract into a NEW stage. Never replay retirement or reinstall accepted Evolution Data Server.')
    state['reclaimed_bytes'] = state['after_free_bytes'] - free_before
    save()
    print(json.dumps(state))


if __name__ == '__main__':
    main()
