"""Promote the verified Settings payload with its actual native runtime inventory."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_native_elf import target_resolve
from package_copyright import write_copyright
from qualify_control_center import ROOT, WORK, ARCHIVES, digest, qualify
from verify_stage import inspect_stage

TARGET = Path('/mnt/lfs')


def runtime_dependencies(stage):
    owners = {}
    versions = {}
    query = '-f=' + '${Package} ${Version}\n'
    listing = subprocess.check_output(['chroot', str(TARGET), 'dpkg-query', '-W', query], text=True)
    for line in listing.splitlines():
        name, version = line.split()
        versions[name] = version
        paths = TARGET / 'var/lib/dpkg/info' / (name + '.list')
        if paths.exists():
            for path in paths.read_text().splitlines():
                owners.setdefault(path, set()).add(name)
    linked = {}
    programs = []
    for path in stage.rglob('*'):
        if path.is_file() and not path.is_symlink():
            with path.open('rb') as stream:
                if stream.read(4) != b'\x7fELF':
                    continue
            programs.append(path)
    assert len(programs) == 4
    for path in programs:
        virtual = '/' + path.relative_to(TARGET).as_posix()
        linkage = subprocess.check_output(['chroot', str(TARGET), 'ldd', virtual], text=True)
        assert 'not found' not in linkage and '/build/' not in linkage and '/src/' not in linkage
        for path in re.findall(r'=> (/[^\s]+)', linkage):
            _, canonical = target_resolve(TARGET, path)
            candidates = owners.get(path, owners.get(canonical, set()))
            assert len(candidates) == 1, (path, candidates)
            owner = next(iter(candidates))
            linked[owner] = versions[owner]
    assert len(linked) == 89
    return linked


def main():
    entries, sources = qualify()
    source = WORK / 'stage'
    versions = runtime_dependencies(source)
    promoted = WORK / 'promotion-1'
    destination = TARGET / 'sources/stage/phase2-gnome-control-center'
    assert all(not os.path.lexists(p) for p in (promoted, destination))
    assert not Path('/var/cache/toddy/packages/gnome-control-center_50.4-1+toddy1_amd64.deb').exists()
    space = os.statvfs(TARGET)
    assert space.f_bavail * space.f_frsize >= 16 * 1024**3 + 27 * 1024**2
    shutil.copytree(source, promoted, symlinks=True)
    assert inspect_stage(promoted)['entries'] == entries
    for row in sources:
        path = TARGET / 'sources' / row['filename']
        if path.exists():
            assert not path.is_symlink() and digest(path) == row['sha256']
        else:
            path.touch(mode=0o644)
            subprocess.run(['mount', '--bind', str(ARCHIVES / row['filename']), str(path)], check=True)
            subprocess.run(['mount', '-o', 'remount,bind,ro,nosuid,nodev,noexec', str(path)], check=True)
            assert digest(path) == row['sha256']
    destination.mkdir(mode=0o755)
    subprocess.run(['mount', '--bind', str(promoted), str(destination)], check=True)
    archives = [row['filename'] for row in sources]
    write_copyright(destination, 'gnome-control-center', archives)
    docs = destination / 'usr/share/doc/gnome-control-center'
    (docs / 'runtime-packages.json').write_text(json.dumps(versions, indent=2) + '\n')
    (docs / 'README.Toddy').write_text('GNOME Control Center 50.4 with the pinned native runtime, '
        'bundled GVC/libgxdp and exact Tecla 50.0 source. Four portable programs, compiled panel metadata, '
        'invalid-option refusal and recovery verified. Shared-schema integration and native graphical actions pending.\n')
    dependencies = ', '.join(name + ' (>= ' + version + ')' for name, version in sorted(versions.items()))
    subprocess.run([sys.executable, str(ROOT / 'scripts/build/stage_package.py'), 'gnome-control-center',
                    '50.4-1+toddy1', str(destination), *[arg for archive in archives for arg in ('--source', archive)],
                    '--recipe', 'scripts/build/phase2/gnome-control-center-install.sh', '--depends', dependencies,
                    '--install'], cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
