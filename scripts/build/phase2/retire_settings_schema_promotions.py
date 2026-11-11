"""Retire two exact closed GTK metadata promotion replicas for Settings integration."""
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

TARGET = Path('/mnt/lfs')
LOG = Path('/var/log/toddy/phase2')
PROFILES = (
    ('gtk', '4.22.4-1+toddy9', 'phase2-gtk-editor-schema-union', 9503390,
     'fef35462b599b404b0df5e68ad290f37f8c6a59879b9f2065bf2bd93607968c9',
     '9c99cbf271566b44efcdf369ccba0ed9e2f3549819e7bf736f189209dd0533b5'),
    ('gtk3', '3.24.52-1+toddy2', 'phase2-gtk3-ibus-cache', 8336206,
     '953928c07f531bf190fbb27bb97c332c4d400c8f4f6a5ea2a549f0c0e99f824d',
     '658601ca770907cd84b191465782f814600c5dc772c51c51918a58d087fbd71e'),
)


def free():
    space = os.statvfs(TARGET)
    return space.f_bavail * space.f_frsize


def controls(path):
    return {p.relative_to(path).as_posix(): digest(p) for p in path.rglob('*')
            if p.is_file() and not p.is_symlink()}


def main():
    subprocess.run(['bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    with Path('/var/log/toddy/build/build.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
        receipt = LOG / 'settings-schema-promotion-custody-1.json'
        part = receipt.with_suffix('.part')
        assert not receipt.exists() and not part.exists(), 'Inspect prior operation; never replay uncertain custody'
        mounts = [Path(p) for p in subprocess.check_output(['findmnt', '-rn', '-o', 'TARGET'], text=True).splitlines()]
        rows = []
        for name, version, stage_name, inode, record_sha, archive_sha in PROFILES:
            record_path = Path('/var/log/toddy/packages') / f'{name}_{version}_amd64.json'
            archive = Path('/var/cache/toddy/packages') / f'{name}_{version}_amd64.deb'
            assert digest(record_path) == record_sha
            record = json.loads(record_path.read_text())
            assert record['installed'] and digest(archive) == record['archive_sha256'] == archive_sha
            assert subprocess.check_output(['chroot', str(TARGET), 'dpkg-query', '-W', '-f=${Status} ${Version}', name], text=True) == 'install ok installed ' + version
            stage = TARGET / 'sources/stage' / stage_name
            assert stage.resolve() == stage and stage.stat().st_ino == inode
            assert stage.stat().st_dev == TARGET.stat().st_dev and not (stage / 'usr').is_symlink()
            assert not any(p.is_relative_to(stage) for p in mounts)
            verify_package_stage(stage, record['payload'])
            for relative, entry in record['payload'].items():
                path = TARGET / relative.lstrip('/')
                if 'sha256' in entry:
                    assert path.is_file() and not path.is_symlink() and digest(path) == entry['sha256'], relative
                if 'symlink' in entry:
                    assert path.is_symlink() and os.readlink(path) == entry['symlink'], relative
            retained = controls(stage / 'DEBIAN')
            assert retained
            rows.append({'name':name, 'version':version, 'stage':str(stage), 'inode':inode,
                         'archive':str(archive), 'archive_sha256':archive_sha,
                         'record':str(record_path), 'record_sha256':record_sha,
                         'control_files':retained, 'state':'verified'})
        before = snapshot()
        state = {'state':'verified', 'before_free_bytes':free(), 'packages':rows,
                 'scope':'Only two verified closed usr promotion replicas. Reuse qualified native archives, retain package records/control and original sources/compiler/workstages. No installed payload or source mutation.'}

        def save():
            with part.open('x') as output:
                output.write(json.dumps(state, indent=2)+'\n')
                output.flush()
                os.fsync(output.fileno())
            part.replace(receipt)

        save()
        for row in rows:
            stage = Path(row['stage'])
            row['state'] = 'retiring'
            save()
            shutil.rmtree(stage / 'usr')
            (stage / '.toddy-retired.json').write_text(json.dumps({'receipt':str(receipt),
                'archive':row['archive'], 'archive_sha256':row['archive_sha256']}, indent=2)+'\n')
            assert controls(stage / 'DEBIAN') == row['control_files']
            assert digest(Path(row['archive'])) == row['archive_sha256']
            assert digest(Path(row['record'])) == row['record_sha256']
            row['state'] = 'retired'
            save()
        assert snapshot() == before
        state.update(state='complete', installed_root_changed_paths=0, after_free_bytes=free(),
                     recovery='Verify retained archive and record, then extract into a new stage. Never replay custody or reinstall accepted GTK runtime.')
        state['reclaimed_bytes'] = state['after_free_bytes'] - state['before_free_bytes']
        save()
        print(json.dumps(state))


if __name__ == '__main__':
    main()
