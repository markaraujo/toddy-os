"""Retire only two closed editor-dependency promotion replicas, not build caches."""
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
    receipt = Path('/var/log/toddy/phase2/editor-dependency-promotion-stage-custody-1.json')
    assert not receipt.exists() and not receipt.with_suffix('.part').exists(), 'Reconcile actual custody; never replay'
    selected = [
        ('tinysparql', '3.11.1', 'b02-tinysparql-install', 'tinysparql-1',
         '00926d1ffc08af1d8f800512e436f1e9d93e25abcffa3d7773e09e8d9d549094'),
        ('exiv2', '0.28.8', 'b02-exiv2-install-2', 'exiv2-1',
         '2c5a7cb6c66a871623f30bbc36bc018b320ed452ff0cf68c874da45a57160cea'),
    ]
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
        status = subprocess.check_output(['chroot', '/mnt/lfs', 'dpkg-query', '-W', '-f=${Status} ${Version}', name], text=True)
        assert status == 'install ok installed ' + version + '-1+toddy1'
        mounts = subprocess.check_output(['findmnt', '-rn', '-o', 'TARGET'], text=True).splitlines()
        assert not any(Path(m) == stage or Path(m).is_relative_to(stage) for m in mounts)
        rows.append({'name': name, 'stage': str(stage), 'inode': stage.stat().st_ino,
                     'archive': str(archive), 'archive_sha256': expected, 'record_sha256': digest(record_path),
                     'payload_entries': len(record['payload']), 'state': 'verified'})
    before = snapshot()
    state = {'scope': 'Only two new verified promotion replicas; installed packages/original build stages/source/test evidence/native archives retained, no old custody replay or trim',
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
    assert snapshot() == before, 'Installed root changed; retain archives and diagnose'
    state.update(state='complete', installed_root_changed_paths=0,
                 after_free_bytes=shutil.disk_usage('/mnt/lfs').free,
                 recovery='Verify native archive/record SHA and extract to a NEW stage if needed; never reinstall or replay retirement. Original compiler stages, sources and raw tests remain.')
    state['reclaimed_bytes'] = state['after_free_bytes'] - state['before_free_bytes']
    save()
    print(json.dumps({k: state[k] for k in ['state', 'reclaimed_bytes', 'installed_root_changed_paths']}))


if __name__ == '__main__':
    main()
