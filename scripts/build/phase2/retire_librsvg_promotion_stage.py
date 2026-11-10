"""Retire only the exact closed Librsvg promotion replica for native headroom."""
from pathlib import Path
import fcntl
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_step import snapshot
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
    receipt = Path('/var/log/toddy/phase2/librsvg-promotion-custody-1.json')
    assert not receipt.exists() and not receipt.with_suffix('.part').exists(), 'Reconcile actual state; never replay'
    native = json.loads((build / 'b02-librsvg-install.success.json').read_text())
    assert native['recipe_exit'] == native['postcheck_exit'] == 0
    record_path = Path('/var/log/toddy/packages/librsvg_2.62.3-1+toddy1_amd64.json')
    assert digest(record_path) == 'a6214854c21846cae981b1a5def86cf89971b1e3c3fd0aa40eb6c8b01ce50554'
    record = json.loads(record_path.read_text())
    assert record['installed'] and not record['generated_paths']
    archive = Path('/var/cache/toddy/packages/librsvg_2.62.3-1+toddy1_amd64.deb')
    archive_sha = '8ea71609cd4cd23b56e43b9a90695640ad134e10af68575e592178098961ca15'
    assert not archive.is_symlink() and digest(archive) == record['archive_sha256'] == archive_sha
    target = Path('/mnt/lfs')
    assert subprocess.check_output(['chroot', str(target), 'dpkg-query', '-W', '-f=${Status} ${Version}', 'librsvg'], text=True) == 'install ok installed 2.62.3-1+toddy1'
    stage = target / 'sources/stage/phase2-librsvg'
    assert stage.resolve() == stage and stage.stat().st_ino == 2147142
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
    workstage = target / 'sources/phase2/work/librsvg-1/stage'
    assert workstage.is_dir() and workstage.resolve() == workstage
    original = files(workstage)
    assert original
    control = files(stage / 'DEBIAN')
    assert control
    before = snapshot()
    free_before = shutil.disk_usage(target).free
    state = {'state': 'verified', 'stage': str(stage), 'stage_inode': stage.stat().st_ino,
             'archive_sha256': archive_sha, 'record_sha256': digest(record_path),
             'workstage_files_retained': len(original), 'before_free_bytes': free_before,
             'scope': 'Only closed Librsvg promotion usr replica; original compiler/source/workstage/archives/DEBIAN and installed payload retained'}

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
    assert files(stage / 'DEBIAN') == control and files(workstage) == original
    assert digest(archive) == archive_sha and snapshot() == before
    state.update(state='complete', installed_root_changed_paths=0, after_free_bytes=shutil.disk_usage(target).free,
                 recovery='Verify retained archive/record then extract into a NEW stage. Never replay retirement or reinstall accepted Librsvg.')
    state['reclaimed_bytes'] = state['after_free_bytes'] - free_before
    save()
    print(json.dumps(state))


if __name__ == '__main__':
    main()
