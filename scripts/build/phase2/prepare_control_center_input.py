"""Prepare exact Settings sources on the already verified private build tmpfs."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from source_filter import source_filter, validate_source_members

ROOT = Path('/opt/toddy-build')
BASE = Path('/run/toddy-samba-client-1')
TARGET = Path('/mnt/lfs')
LOG = Path('/var/log/toddy/phase2')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def available(path):
    space = os.statvfs(path)
    return space.f_bavail * space.f_frsize


def extract(archive, destination, root_name):
    with tarfile.open(archive) as bundle:
        members = bundle.getmembers()
        assert members and all(Path(member.name).parts[0] == root_name for member in members)
        assert sum(member.size for member in members if member.isfile()) <= 64 * 1024**2
        validate_source_members(archive.name, members)
        checked = source_filter(archive.name)
        for member in members:
            checked(member, destination)
        bundle.extractall(destination, filter=checked)


def main():
    subprocess.run(['bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    with Path('/var/log/toddy/build/build.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
        previous = json.loads((LOG / 'samba-client-tmpfs-1.json').read_text())
        assert previous['state'] == 'prepared'
        assert Path('/proc/sys/kernel/random/boot_id').read_text().strip() == previous['boot_id']
        assert subprocess.check_output(['findmnt', '-n', '-o', 'ID', '--mountpoint', str(BASE)], text=True).strip() == previous['mount_id']
        assert available(BASE) >= 768 * 1024**2 and available(TARGET) >= 16 * 1024**3 + 1024**2
        holder = BASE / 'gnome-control-center-input-1'
        source = holder / 'gnome-control-center-50.4'
        work = BASE / 'gnome-control-center-work-1'
        source_alias = TARGET / 'sources/phase2/inputs/gnome-control-center-50.4'
        work_alias = TARGET / 'sources/phase2/work/gnome-control-center-1'
        receipt = LOG / 'gnome-control-center-input-tmpfs-1.json'
        part = receipt.with_suffix('.part')
        assert all(not os.path.lexists(path) for path in (holder, work, source_alias, work_alias, receipt, part))
        rows = json.loads((ROOT / 'config/phase2/sources.lock.json').read_text())['components']
        selected = [next(row for row in rows if row['name'] == name) for name in ('gnome-control-center', 'tecla')]
        expected = {row['filename']: row for row in selected}
        state = {'state':'planned', 'boot_id':previous['boot_id'], 'mount_id':previous['mount_id'],
                 'source_alias':str(source_alias), 'work_alias':str(work_alias), 'sources':selected,
                 'target_free_before_bytes':available(TARGET)}

        def save():
            with part.open('x') as output:
                output.write(json.dumps(state, indent=2)+'\n')
                output.flush()
                os.fsync(output.fileno())
            part.replace(receipt)

        save()
        holder.mkdir(mode=0o755)
        archives = holder / 'archives'
        archives.mkdir(mode=0o755)
        received = set()
        with tarfile.open(fileobj=sys.stdin.buffer, mode='r|') as transport:
            for member in transport:
                assert member.isfile() and member.name in expected and member.name not in received
                assert member.size <= 64 * 1024**2
                data = transport.extractfile(member).read()
                assert hashlib.sha256(data).hexdigest() == expected[member.name]['sha256']
                with (archives / member.name).open('xb') as output:
                    output.write(data)
                received.add(member.name)
        assert received == set(expected)
        extract(archives / selected[0]['filename'], holder, 'gnome-control-center-50.4')
        extract(archives / selected[1]['filename'], source / 'subprojects', 'tecla-50.0')
        assert not (source / 'subprojects/tecla').exists()
        (source / 'subprojects/tecla-50.0').rename(source / 'subprojects/tecla')
        assert '1fe6de799f39b3126e8d0db66fa4f16c10fd9bd6' in (source / 'subprojects/libgxdp.wrap').read_text()
        assert "version: '48.alpha'" in (source / 'subprojects/libgxdp/meson.build').read_text()
        recipe = ROOT / 'scripts/build/phase2/gnome-control-center-build.sh'
        (source / 'toddy-build.sh').write_bytes(recipe.read_bytes())
        prepared = {'source_sha256':selected[0]['sha256'], 'additional_sources':[selected[1]],
                    'recipe_sha256':digest(recipe), 'source_patches':[],
                    'scope':'Bundled GVC/libgxdp and exact frozen Tecla source. All other dependency fallbacks disabled.'}
        (source / 'toddy-prepared.json').write_text(json.dumps(prepared, indent=2)+'\n')
        work.mkdir(mode=0o755)
        os.chown(work, 101, 101)
        for src, dst, readonly in ((source, source_alias, True), (work, work_alias, False)):
            dst.mkdir(mode=0o755)
            subprocess.run(['mount', '--bind', str(src), str(dst)], check=True)
            flags = 'remount,bind,nosuid,nodev' + (',ro' if readonly else '')
            subprocess.run(['mount', '-o', flags, str(dst)], check=True)
            options = set(subprocess.check_output(['findmnt', '-n', '-o', 'OPTIONS', '--mountpoint', str(dst)], text=True).strip().split(','))
            assert {'nosuid', 'nodev', 'ro' if readonly else 'rw'} <= options
            assert dst.stat().st_ino == src.stat().st_ino
        assert available(TARGET) >= 16 * 1024**3 and state['target_free_before_bytes'] - available(TARGET) <= 1024**2
        assert available(BASE) >= 640 * 1024**2
        state.update(state='prepared', source_inode=source.stat().st_ino, work_inode=work.stat().st_ino,
                     target_free_bytes=available(TARGET), scratch_free_bytes=available(BASE),
                     prepared_sha256=digest(source / 'toddy-prepared.json'))
        save()
        print(json.dumps(state))


if __name__ == '__main__':
    main()
