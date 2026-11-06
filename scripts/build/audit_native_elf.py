#!/usr/bin/env python3
"""Inspect actual native ELF dependencies without following links into the builder."""
from collections import defaultdict
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess

HERE = Path(__file__).resolve().parent
TARGET = Path('/mnt/lfs')


def target_resolve(root, virtual):
    pending = list(PurePosixPath(virtual).parts)
    resolved = []
    links = 0
    while pending:
        part = pending.pop(0)
        if part in ('/', '.', ''):
            continue
        if part == '..':
            if resolved:
                resolved.pop()
            continue
        path = root.joinpath(*resolved, part)
        if path.is_symlink():
            links += 1
            if links > 40:
                raise ValueError('Target symlink loop')
            link = PurePosixPath(os.readlink(path))
            if link.is_absolute():
                resolved = []
            pending = list(link.parts) + pending
        else:
            resolved.append(part)
    return root.joinpath(*resolved), '/' + '/'.join(resolved)


def main():
    subprocess.run(['bash', '-c', 'source "$1"; guard_target', 'guard', str(HERE / 'target.sh')], check=True)
    lines = subprocess.check_output(['dpkg-query', '--admindir=' + str(TARGET / 'var/lib/dpkg'),
                                     '-W', '-f=${Package}\t${Version}\t${Status}\t${Depends}\n'], text=True).splitlines()
    packages = {}
    owners = defaultdict(set)
    for line in lines:
        name, version, status, depends = line.split('\t')
        if status != 'install ok installed':
            continue
        metadata = Path('/var/log/toddy/packages') / f'{name}_{version}_amd64.json'
        if not metadata.exists():
            metadata = metadata.with_name(f'{name}_{version}_all.json')
        record = json.loads(metadata.read_text())
        declared = set(re.findall(r'(?:^|[,|])\s*([a-z0-9][a-z0-9+.-]*)', depends))
        packages[name] = (record, declared)
        for path, entry in record['payload'].items():
            if not entry.get('directory'):
                owners[path].add(name)
    findings = []
    elf_count = 0
    for name, (record, declared) in sorted(packages.items()):
        for virtual, entry in record['payload'].items():
            if not entry.get('sha256'):
                continue
            path, canonical = target_resolve(TARGET, virtual)
            if not path.is_file():
                findings.append({'package': name, 'file': virtual, 'problem': 'recorded file missing'})
                continue
            with path.open('rb') as stream:
                if stream.read(4) != b'\x7fELF':
                    continue
            elf_count += 1
            dynamic = subprocess.check_output(['readelf', '-d', str(path)], text=True)
            entries = re.findall(r'\((NEEDED|RPATH|RUNPATH)\).*\[(.*?)\]', dynamic)
            search_dirs = []
            for kind, value in entries:
                if kind in ('RPATH', 'RUNPATH'):
                    if any(fragment in value for fragment in ('/sources', '/tools', '/mnt/lfs', 'x86_64-lfs-linux-gnu')):
                        findings.append({'package': name, 'file': virtual, 'problem': 'build path in runtime search', 'value': value})
                    for directory in value.split(':'):
                        directory = directory.replace('${ORIGIN}', str(PurePosixPath(canonical).parent)).replace('$ORIGIN', str(PurePosixPath(canonical).parent))
                        if directory.startswith('/') and '$' not in directory:
                            search_dirs.append(directory)
                        else:
                            findings.append({'package': name, 'file': virtual, 'problem': 'loader search token needs manual review', 'value': directory})
            search_dirs += ['/usr/lib', '/lib']
            for kind, value in entries:
                if kind != 'NEEDED':
                    continue
                found = None
                for directory in search_dirs:
                    requested = directory.rstrip('/') + '/' + value
                    provider_file, provider_virtual = target_resolve(TARGET, requested)
                    if provider_file.is_file():
                        found = (provider_virtual, owners.get(provider_virtual, set()) | owners.get(requested, set()))
                        break
                if found is None:
                    findings.append({'package': name, 'file': virtual, 'needed': value, 'problem': 'provider absent from reviewed native search paths'})
                    continue
                provider_virtual, providers = found
                if not providers:
                    findings.append({'package': name, 'file': virtual, 'needed': value, 'problem': 'temporary or unowned provider', 'provider': provider_virtual})
                elif name not in providers and not (providers & declared):
                    findings.append({'package': name, 'file': virtual, 'needed': value, 'problem': 'direct native provider undeclared', 'providers': sorted(providers)})
    print(json.dumps({'scope': 'direct ELF dependencies of installed native package files',
                      'release_complete': False, 'packages': len(packages), 'elf_files': elf_count,
                      'findings': findings,
                      'limitations': ['Does not prove optional dlopen, executable-tool, data/plugin or license closure.',
                                      'Nondefault loader search paths require separate review; version constraints require native package-manager tests.']}, indent=2))


if __name__ == '__main__':
    main()
