#!/usr/bin/env python3
"""Create/install a project-built .deb from a staging root in the build guest.

The build host supplies dpkg tooling only. No foreign binary package or
maintainer script is imported. Check ownership before target mutation; use
explicit recipe postconditions and cold checkpoints for update recovery.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from locked_inputs import locked_source
from provenance import recipe_set
from package_backend import PackageBackend
from source_notices import retain_source_notices
from package_ownership import normalize_ownership

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TARGET = Path('/mnt/lfs')
CACHE = Path('/var/cache/toddy/packages')
RECORDS = Path('/var/log/toddy/packages')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def payload(stage):
    entries = {}
    for base, directories, files in os.walk(stage, followlinks=False):
        for name in directories + files:
            path = Path(base) / name
            relative = '/' + str(path.relative_to(stage))
            if any(c in relative for c in '\n\r\t'):
                raise SystemExit('Control characters in package path rejected')
            st = path.lstat()
            row = {'mode': st.st_mode, 'uid': st.st_uid, 'gid': st.st_gid}
            if path.is_symlink():
                row['symlink'] = os.readlink(path)
            elif path.is_file():
                row['sha256'] = digest(path)
            elif path.is_dir():
                row['directory'] = True
            else:
                raise SystemExit(f'Special device/socket in package rejected: {relative}')
            entries[relative] = row
    return entries



def canonicalize_usrmerge(stage):
    """Match the book target's bin/lib/sbin aliases without losing files."""
    def merge(source, destination):
        if source.is_dir() and not source.is_symlink():
            if destination.is_symlink() or (destination.exists() and not destination.is_dir()):
                raise SystemExit(f'Staged usrmerge directory collision: {destination}')
            if not destination.exists():
                destination.mkdir(parents=True)
                shutil.copystat(source, destination)
            for child in list(source.iterdir()):
                merge(child, destination/child.name)
            source.rmdir()
        else:
            if destination.exists() or destination.is_symlink():
                raise SystemExit(f'Staged usrmerge payload collision: {destination}')
            source.rename(destination)
    for name in ('bin','lib','sbin'):
        source=stage/name
        if source.is_dir() and not source.is_symlink():
            merge(source,stage/'usr'/name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name')
    parser.add_argument('version')
    parser.add_argument('stage', type=Path)
    parser.add_argument('--recipe', type=Path, required=True)
    parser.add_argument('--architecture', choices=['amd64', 'all'], default='amd64')
    parser.add_argument('--depends', default='')
    parser.add_argument('--source', action='append', default=[])
    parser.add_argument('--conffile', action='append', default=[])
    parser.add_argument('--install', action='store_true', help='Otherwise validate/build archive without installing')
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise SystemExit('Requires disposable-guest root')
    subprocess.run(['bash', '-c', 'source "$1"; guard_target', 'guard', str(HERE/'target.sh')], check=True)
    if not re.fullmatch(r'[a-z0-9][a-z0-9+.-]+', args.name):
        raise SystemExit('Invalid native package name')
    if not re.fullmatch(r'[0-9][0-9A-Za-z.+:~_-]*', args.version) or '\n' in args.depends:
        raise SystemExit('Invalid native package version/dependency field')
    backend = PackageBackend(TARGET)
    backend.run('dpkg', '--validate-version', args.version)
    stage = args.stage.resolve()
    if args.stage.is_symlink() or not stage.is_relative_to(TARGET/'sources/stage') or not stage.is_dir():
        raise SystemExit('Staging root must be a real directory under target sources/stage')
    if stage == TARGET/'sources/stage':
        raise SystemExit('Select one package staging directory')
    if (stage/'DEBIAN').exists() or (stage/'DEBIAN').is_symlink() or (stage/'usr/lib64').exists() or (stage/'usr/lib64').is_symlink():
        raise SystemExit('Unexpected control directory or non-LFS /usr/lib64')
    if not args.recipe.resolve().is_relative_to(ROOT/'scripts') or not args.recipe.is_file():
        raise SystemExit('Recipe provenance must be a project script')
    canonicalize_usrmerge(stage)
    retain_source_notices(ROOT, TARGET, stage, args.name, args.source)
    normalized_ownership = normalize_ownership(ROOT, TARGET, stage, args.name)
    generated_paths=[]
    info_index=stage/'usr/share/info/dir'
    if info_index.exists() or info_index.is_symlink():
        info_index.unlink()
        generated_paths.append('/usr/share/info/dir')
    entries = payload(stage)
    if not entries:
        raise SystemExit('Empty package')
    for path in entries:
        if path in ('/tools', '/sources') or path.startswith(('/tools/', '/sources/', '/bin/', '/lib/', '/sbin/')):
            raise SystemExit(f'Temporary or noncanonical merged-usr payload: {path}')
        if path in ('/bin', '/lib', '/sbin') and entries[path].get('symlink') != 'usr'+path:
            raise SystemExit(f'Noncanonical root alias: {path}')
    ownership = {}
    database = TARGET/'var/lib/dpkg'
    if (database/'info').exists():
        for listing in (database/'info').glob('*.list'):
            owner = listing.name.removesuffix('.list')
            for path in listing.read_text().splitlines():
                ownership.setdefault(path.rstrip('/'), set()).add(owner)
    conflicts = []
    for path, entry in entries.items():
        if entry.get('directory'):
            continue
        owners = ownership.get(path, set()) - {args.name, args.name+':'+args.architecture}
        if owners:
            conflicts.append({'path': path, 'owners': sorted(owners)})
    if conflicts:
        raise SystemExit('Native package ownership conflict before install: '+json.dumps(conflicts))
    sources = json.loads((ROOT/'config/sources.lock.json').read_text())
    if sources['status'] != 'verified':
        raise SystemExit('Baseline source lock not verified')
    source_rows = []
    for name in args.source:
        row = locked_source(ROOT, name)
        if not row or digest(TARGET/'sources'/name) != row['sha256']:
            raise SystemExit(f'Source provenance/integrity mismatch: {name}')
        source_rows.append(row)
    for path in args.conffile:
        if not path.startswith('/etc/') or not entries.get(path, {}).get('sha256'):
            raise SystemExit(f'Conffile must be a packaged regular /etc file: {path}')
    copyright_file = stage/'usr/share/doc'/args.name/'copyright'
    if not copyright_file.is_file():
        raise SystemExit('Native package requires retained upstream/project copyright notices')
    CACHE.mkdir(parents=True, exist_ok=True)
    archive = CACHE/f'{args.name}_{args.version}_{args.architecture}.deb'
    if archive.exists():
        raise SystemExit('Native archive already exists; preserve/inspect before rebuilding')
    control = stage/'DEBIAN'
    control.mkdir()
    text = (f'Package: {args.name}\nVersion: {args.version}\nArchitecture: {args.architecture}\n'
            'Maintainer: Toddy OS Development <noreply@example.invalid>\n'
            f'Description: Toddy OS source-built {args.name}\n')
    if args.depends:
        text += f'Depends: {args.depends}\n'
    (control/'control').write_text(text)
    if args.conffile:
        (control/'conffiles').write_text('\n'.join(args.conffile)+'\n')
    RECORDS.mkdir(parents=True, exist_ok=True)
    backend.build(stage, archive)
    record = {'name': args.name, 'version': args.version, 'archive_sha256': digest(archive),
        'recipe_sha256': digest(args.recipe), 'packager_sha256': digest(Path(__file__)), 'packaging_backend': backend.record,
        'supporting_build_scripts': recipe_set(), 'sources': source_rows,
        'book_sources': json.loads((ROOT/'config/books.lock.json').read_text()),
        'ownership_policy_sha256': digest(ROOT/'config/package-ownership-policy.json'),
        'normalized_build_ownership': normalized_ownership,
        'source_kind': 'upstream-archives-and-versioned-recipe' if source_rows else 'book-derived-versioned-recipe',
        'payload': entries, 'generated_paths': generated_paths,
        'runtime_dependency_closure': 'pending final base audit', 'installed': False}
    record_path = RECORDS/(archive.stem+'.json')
    record_path.write_text(json.dumps(record, indent=2)+'\n')
    if args.install:
        database.mkdir(parents=True, exist_ok=True)
        (database/'status').touch(exist_ok=True)
        # Packages contain no maintainer scripts. Target root is always explicit.
        backend.install(archive)
        for path in entries:
            if path.startswith('/usr/share/info/') and re.search(r'\.info(?:\.(?:gz|xz|bz2))?$',path):
                subprocess.run(['/usr/sbin/chroot',str(TARGET),'/usr/bin/install-info',
                    '--dir-file=/usr/share/info/dir',path],check=True)
        record['installed'] = True
        record_path.write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps({'package': args.name, 'sha256': record['archive_sha256'],
                      'paths': len(entries), 'installed': record['installed']}))


if __name__ == '__main__':
    main()
