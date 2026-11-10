"""Retire only closed cargo-c promotion replica; original compiler stage remains."""
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_step import snapshot
from retire_llvm_stages import digest, verify_package_stage


def main():
    assert os.geteuid() == 0
    subprocess.run(['bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    lock = open('/var/log/toddy/build/build.lock', 'a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    receipt = Path('/var/log/toddy/phase2/cargo-c-promotion-stage-custody-1.json')
    assert not receipt.exists() and not receipt.with_suffix('.part').exists(), 'Reconcile actual custody; never replay'
    selected = [('cargo-c', '0.10.24', 'b02-cargo-c-install', 'cargo-c-1', 'd32a863ce17d454ffd3ecc4987c6184fe473f2336edfb19a6da3c78b660c1da8')]
    rows = []
    for name, version, step, work, expected in selected:
        success = json.loads(Path('/var/log/toddy/build', step + '.success.json').read_text())
        assert success['recipe_exit'] == success['postcheck_exit'] == 0
        record_path = Path('/var/log/toddy/packages', name + '_' + version + '-1+toddy1_amd64.json')
        record = json.loads(record_path.read_text())
        archive = Path('/var/cache/toddy/packages', record_path.stem + '.deb')
        assert record['installed'] and digest(archive) == record['archive_sha256'] == expected
        stage = Path('/mnt/lfs/sources/stage', 'phase2-' + name)
        assert stage.resolve() == stage and not stage.is_symlink()
        assert not (stage / '.toddy-retired.json').exists()
        assert Path('/mnt/lfs/sources/phase2/work', work, 'stage/usr').is_dir()
        verify_package_stage(stage, record['payload'])
        for relative, entry in record['payload'].items():
            installed = Path('/mnt/lfs') / relative.lstrip('/')
            st = installed.lstat()
            assert (st.st_mode,st.st_uid,st.st_gid)==(entry['mode'],entry['uid'],entry['gid'])
            if 'sha256' in entry:assert digest(installed)==entry['sha256']
            if 'symlink' in entry:assert os.readlink(installed)==entry['symlink']
        status = subprocess.check_output(['chroot', '/mnt/lfs', 'dpkg-query', '-W', '-f=${Status} ${Version}', name], text=True)
        assert status == 'install ok installed ' + version + '-1+toddy1'
        mounts = subprocess.check_output(['findmnt', '-rn', '-o', 'TARGET'], text=True).splitlines()
        assert not any(Path(m) == stage or Path(m).is_relative_to(stage) for m in mounts)
        rows.append({'name': name, 'stage': str(stage), 'inode': stage.stat().st_ino,
                     'archive': str(archive), 'archive_sha256': expected, 'record_sha256': digest(record_path),
                     'payload_entries': len(record['payload']), 'state': 'verified'})
    from verify_stage import inspect_stage
    original = Path('/mnt/lfs/sources/phase2/work/cargo-c-1/stage')
    original_before = inspect_stage(original)
    assert original_before['entries']
    before = snapshot()
    state = {'scope': 'Only one new verified cargo-c promotion replica; installed packages/original build stages/source/test evidence/native archives retained, no old custody replay or trim',
             'state': 'verified', 'producer_sha256': digest(Path(__file__)), 'stages': rows, 'before_free_bytes': shutil.disk_usage('/mnt/lfs').free}
    def save():
        part = receipt.with_suffix('.part')
        assert not part.exists()
        with part.open('x') as stream:
            json.dump(state, stream, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        part.replace(receipt)
    save()
    for row in rows:
        stage = Path(row['stage'])
        assert stage.stat().st_ino == row['inode'] and digest(Path(row['archive'])) == row['archive_sha256']
        row['state'] = 'retiring'
        save()
        for name in ['usr', 'etc']:
            path = stage / name
            if path.exists():
                assert path.is_dir() and not path.is_symlink()
                shutil.rmtree(path)
        (stage / '.toddy-retired.json').write_text(json.dumps({'receipt': str(receipt), 'archive': row['archive'],
                                                            'archive_sha256': row['archive_sha256']}, indent=2) + '\n')
        assert not (stage / 'usr').exists()
        row['state'] = 'retired'
        save()
    assert inspect_stage(original) == original_before
    assert snapshot() == before, 'Installed root changed; retain archives and diagnose'
    state.update(state='complete', installed_root_changed_paths=0,
                 after_free_bytes=shutil.disk_usage('/mnt/lfs').free,
                 recovery='Verify native archive/record SHA and extract to a NEW stage if needed; never reinstall or replay retirement. Original compiler stages, sources and raw tests remain.')
    state['reclaimed_bytes'] = state['after_free_bytes'] - state['before_free_bytes']
    save()
    print(json.dumps({k: state[k] for k in ['state', 'reclaimed_bytes', 'installed_root_changed_paths']}))


if __name__ == '__main__':
    main()
