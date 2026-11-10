"""Retire only the exact closed Node.js promotion replica for native headroom."""
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
    receipt = Path('/var/log/toddy/phase2/node-promotion-custody-1.json')
    assert not receipt.exists() and not receipt.with_suffix('.part').exists(), 'Reconcile actual state; never replay'
    native_receipt = build / 'b01-node-native-context.success.json'
    assert digest(native_receipt) == 'ad6577310b9da013da72e4e40735fa67efa10835da7ec2bfd3ab60926b8ffd95'
    native = json.loads(native_receipt.read_text())
    assert native['recipe_exit'] == native['postcheck_exit'] == native['changed_paths'] == 0
    original_receipt = build / 'b01-node-bootstrap-install.failed.json'
    assert digest(original_receipt) == 'c69894c0704bea1771f63e9176b31b6365715bf47468b46b68869547cce1df0a'
    initial = json.loads(original_receipt.read_text())
    assert initial['recipe_exit'] == 0 and initial['postcheck_exit'] == 1
    record_path = Path('/var/log/toddy/packages/nodejs_24.19.0-1+toddy1_amd64.json')
    assert digest(record_path) == '3a322794399583b9b7318a6bb7b7ba6d0d954c55303a3bc9f8128e41191458be'
    record = json.loads(record_path.read_text())
    assert record['installed'] and not record['generated_paths']
    archive = Path('/var/cache/toddy/packages/nodejs_24.19.0-1+toddy1_amd64.deb')
    archive_sha = '51c69c2f4eff6fb5473432f24f78b0140346aa50f9aa0213cd0381dcf40fa917'
    assert not archive.is_symlink() and digest(archive) == record['archive_sha256'] == archive_sha
    target = Path('/mnt/lfs')
    assert subprocess.check_output(['chroot', str(target), 'dpkg-query', '-W', '-f=${Status} ${Version}', 'nodejs'], text=True) == 'install ok installed 24.19.0-1+toddy1'
    stage = target / 'sources/stage/phase2-node-bootstrap'
    assert stage.resolve() == stage and stage.stat().st_ino == 7534318
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
    workstage = target / 'sources/phase2/work/node-bootstrap-1/stage'
    assert workstage.is_dir() and workstage.resolve() == workstage
    original = inspect_stage(workstage)
    assert original['manifest_sha256'] == '539c67cd13cc5b40cb386e89f8b893c6c65677ef29916301120517dcfc54ba67'
    control = files(stage / 'DEBIAN')
    assert control
    before = snapshot()
    free_before = shutil.disk_usage(target).free
    state = {'state': 'verified', 'stage': str(stage), 'stage_inode': stage.stat().st_ino,
             'archive_sha256': archive_sha, 'record_sha256': digest(record_path),
             'workstage_manifest_sha256': original['manifest_sha256'], 'before_free_bytes': free_before,
             'scope': 'Only closed Node.js promotion usr replica; original compiler/source/workstage/archives/DEBIAN and installed payload retained'}

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
                 recovery='Verify retained archive/record then extract into a NEW stage. Never replay retirement or reinstall accepted Node.js.')
    state['reclaimed_bytes'] = state['after_free_bytes'] - free_before
    save()
    print(json.dumps(state))


if __name__ == '__main__':
    main()
