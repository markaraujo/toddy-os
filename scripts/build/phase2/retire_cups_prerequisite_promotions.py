"""Retire three exact closed promotion replicas; keep sources/compiler/workstage."""
from pathlib import Path
import fcntl
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_step import snapshot
from stage_package import payload
from retire_llvm_stages import digest

ROWS = [
    ('libqmi', '1.38.0', 'b02-libqmi-verify-3', 4672,
     '321c69ecbc8cc74b60683b3fd32e6f87832e389f675f648aeb6591b7cf1f9ef7',
     '364fed7bd84d3d9f9acee17ac431dcb01bbd8a90a4c729a2daf6eb81665a65fa'),
    ('mitkrb', '1.22.2', 'b02-mitkrb-install', 17832,
     '15af322020ca2122b9f572b31553be5246f2c7409a0d77d3e528555bd929fd14',
     'b34b8d324dd82680ea50c0ddfa6db4d649d7c807f9b73e6d39b2fe75983924c1'),
    ('gweather-locations', '2026.2', 'b02-gweather-locations-install-2', 8336241,
     'beed18af2744f8a92356af2b4b7c26fb4fd8d8cdb62445cebd0dd072f70a8a9b',
     '8c87cef2a7e26e0341937a03c3fe79d3e9216e39cefcbaf48035e425664e20dd'),
]


def free(path):
    value = os.statvfs(path)
    return value.f_bavail * value.f_frsize


def main():
    assert os.geteuid() == 0
    subprocess.run(['bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    build = Path('/var/log/toddy/build')
    lock = (build / 'build.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert not list(build.glob('*.running.json')) and not (build / 'input-sync.running').exists()
    log = Path('/var/log/toddy/phase2')
    receipt = log / 'cups-prerequisite-promotion-custody-1.json'
    assert not receipt.exists() and not receipt.with_suffix('.part').exists(), 'Reconcile real state; never replay custody'
    target = Path('/mnt/lfs')
    scratch = target / 'sources/phase2/work/doxygen-1'
    root = Path('/opt/toddy-build')
    from shared_source_inputs import volume
    volume(scratch)
    from qualify_libqmi import qualify as qmi
    from qualify_mitkrb import qualify as kerberos
    from qualify_gweather_locations import qualify as locations
    qualifiers = {'libqmi': qmi, 'mitkrb': kerberos, 'gweather-locations': locations}
    mounts = [Path(x) for x in subprocess.check_output(['findmnt', '-rn', '-o', 'TARGET'], text=True).splitlines()]
    verified = []
    for name, version, step, inode, record_sha, archive_sha in ROWS:
        passed = json.loads((build / (step + '.success.json')).read_text())
        assert passed['recipe_exit'] == passed['postcheck_exit'] == 0
        record_path = Path('/var/log/toddy/packages') / (name + '_' + version + '-1+toddy1_amd64.json')
        assert digest(record_path) == record_sha
        record = json.loads(record_path.read_text())
        assert record['installed'] and record['generated_paths'] == []
        archive = Path('/var/cache/toddy/packages') / (record_path.stem + '.deb')
        assert archive.is_file() and not archive.is_symlink() and digest(archive) == record['archive_sha256'] == archive_sha
        assert subprocess.check_output(['chroot', str(target), 'dpkg-query', '-W', '-f=${Status} ${Version}', name], text=True) == 'install ok installed ' + version + '-1+toddy1'
        stage = target / 'sources/stage' / ('phase2-' + name)
        assert stage.resolve() == stage and stage.stat().st_ino == inode
        expected_roots = {'usr', 'run', 'var', 'DEBIAN'} if name == 'mitkrb' else {'usr', 'DEBIAN'}
        assert {x.name for x in stage.iterdir()} == expected_roots
        assert stage.stat().st_dev == (target if name == 'gweather-locations' else scratch).stat().st_dev
        actual = {p: row for p, row in payload(stage).items() if p != '/DEBIAN' and not p.startswith('/DEBIAN/')}
        assert actual == record['payload'], 'Unknown or changed promotion payload; preserve it'
        for path, row in record['payload'].items():
            installed = target / path.lstrip('/')
            if 'sha256' in row:
                assert digest(installed) == row['sha256']
            if 'symlink' in row:
                assert os.readlink(installed) == row['symlink']
        assert not any(p == stage / 'usr' or p.is_relative_to(stage / 'usr') for p in mounts)
        control = {str(p.relative_to(stage)): digest(p) for p in (stage / 'DEBIAN').rglob('*') if p.is_file()}
        assert control
        proof = qualifiers[name](root)
        verified.append((stage, archive, proof, control))
    before = snapshot()
    state = {'state': 'verified', 'scope': 'Only three archive-identical closed promotion usr replicas. Installed root, original source/compiler/workstage/raw evidence/native archives/DEBIAN and MIT run/var directories retained.',
             'before_free_bytes': {'target': free(target), 'scratch': free(scratch)}, 'completed': []}

    def save():
        part = receipt.with_suffix('.part')
        assert not part.exists()
        with part.open('x') as stream:
            stream.write(json.dumps(state, indent=2) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        part.replace(receipt)

    save()
    for row, (stage, archive, proof, control) in zip(ROWS, verified):
        name, version, step, inode, record_sha, archive_sha = row
        assert stage.stat().st_ino == inode
        state.update(state='retiring', current=name)
        save()
        shutil.rmtree(stage / 'usr')
        (stage / '.toddy-retired.json').write_text(json.dumps({'receipt': str(receipt), 'archive': str(archive), 'archive_sha256': archive_sha}, indent=2) + '\n')
        assert not (stage / 'usr').exists()
        assert control == {str(p.relative_to(stage)): digest(p) for p in (stage / 'DEBIAN').rglob('*') if p.is_file()}
        assert digest(archive) == archive_sha and qualifiers[name](root) == proof
        state['completed'].append({'name': name, 'stage': str(stage), 'stage_inode': inode, 'record_sha256': record_sha, 'archive_sha256': archive_sha, 'workstage_files_retained': len(proof['stage_sha256'])})
        save()
    assert snapshot() == before, 'Installed root changed; preserve state and diagnose'
    state.update(state='complete', installed_root_changed_paths=0, after_free_bytes={'target': free(target), 'scratch': free(scratch)},
                 recovery='Verify retained native archive/record and extract into a NEW stage when needed. Never replay retirement or reinstall accepted packages.')
    state['reclaimed_bytes'] = {key: state['after_free_bytes'][key] - value for key, value in state['before_free_bytes'].items()}
    save()
    print(json.dumps(state))


if __name__ == '__main__':
    main()
