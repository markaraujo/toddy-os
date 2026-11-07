"""Check native executable linkage and shebang availability inside a private image.

Use the image's own loader in a chroot; never run a workload or use builder
libraries to satisfy image dependencies. Package solver, optional dlopen/data
requirements, symbol execution and boot acceptance remain separate checks.
"""
import hashlib
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess

from audit_native_elf import target_resolve
import package_database

ENVIRONMENT = {'PATH': '/usr/bin:/usr/sbin', 'LC_ALL': 'C', 'HOME': '/root'}
LOADER = '/lib64/ld-linux-x86-64.so.2'
CANONICAL_LOADER = '/usr/lib/ld-linux-x86-64.so.2'


def private_image(backend, image):
    image = Path(image)
    if (not backend.native or os.geteuid() != 0 or image.resolve() != image or not image.is_dir()
            or not any(image != backend.target / area and image.is_relative_to(backend.target / area)
                       for area in ('tmp', 'sources/stage'))):
        raise ValueError('Runtime audit requires a private canonical native image')
    preload = image / 'etc/ld.so.preload'
    if preload.exists() or preload.is_symlink():
        raise ValueError('Image preload configuration needs separate explicit review')
    return image


def owned_file(image, virtual, entries, *, executable=False):
    if not virtual.startswith('/') or any(part in virtual for part in ('/sources/', '/tools/', '/mnt/lfs/')):
        raise ValueError('Runtime input uses a noncanonical or build-only path')
    path, canonical = target_resolve(image, virtual)
    row = entries.get(canonical, {})
    if not row.get('sha256'):
        raise ValueError('Runtime input lacks native regular-file ownership: ' + virtual)
    current = path.lstat()
    if (not stat.S_ISREG(current.st_mode) or current.st_dev != image.stat().st_dev
            or (current.st_mode, current.st_uid, current.st_gid) != (row['mode'], row['uid'], row['gid'])
            or executable and not current.st_mode & 0o111):
        raise ValueError('Runtime input metadata/type/execute permission differs: ' + virtual)
    with path.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != row['sha256']:
            raise ValueError('Runtime input bytes differ: ' + virtual)
    return path, canonical


def shebang(image, virtual, first, entries):
    # Linux passes the optional argument as one string. Only env -S explicitly
    # splits it. Refuse unsupported launch syntax instead of guessing a PATH.
    if b'\n' not in first[:256]:
        raise ValueError('Shebang exceeds the reviewed kernel line bound: ' + virtual)
    raw = first[2:].decode('utf-8').strip()
    words = raw.split(None, 1)
    if not words or not words[0].startswith('/'):
        raise ValueError('Invalid absolute shebang interpreter: ' + virtual)
    interpreter = words[0]
    _, canonical = owned_file(image, interpreter, entries, executable=True)
    result = {'file': virtual, 'interpreter': interpreter, 'owned_interpreter': canonical}
    if canonical == '/usr/bin/env':
        arguments = words[1] if len(words) == 2 else ''
        if arguments.startswith('-S '):
            arguments = shlex.split(arguments[3:])
        elif arguments and not any(char.isspace() for char in arguments):
            arguments = [arguments]
        else:
            raise ValueError('Environment shebang requires reviewed argument splitting: ' + virtual)
        if not arguments or arguments[0].startswith('-') or '=' in arguments[0]:
            raise ValueError('Environment shebang changes unreviewed launch policy: ' + virtual)
        program = arguments[0]
        if '/' in program:
            raise ValueError('Environment shebang requires a simple native command: ' + virtual)
        selected = None
        for directory in ('/usr/bin', '/usr/sbin'):
            candidate = directory + '/' + program
            path, _ = target_resolve(image, candidate)
            if path.exists() or path.is_symlink():
                _, selected = owned_file(image, candidate, entries, executable=True)
                break
        if selected is None:
            raise ValueError('Environment interpreter is absent inside the image: ' + program)
        result['environment_command'] = selected
    return result


def executable(backend, image, virtual, entries):
    image = private_image(backend, image)
    path, canonical = owned_file(image, virtual, entries)
    with path.open('rb') as stream:
        first = stream.readline(4096)
    if first.startswith(b'#!') and entries[canonical]['mode'] & 0o111:
        return {'kind': 'script', **shebang(image, virtual, first, entries)}
    if not first.startswith(b'\x7fELF'):
        return {'kind': 'data', 'file': virtual}
    native_path = '/' + str(path.relative_to(backend.target))
    headers = backend.run('readelf', '-lWd', native_path, capture_output=True, text=True, timeout=30)
    if headers.stderr:
        raise ValueError('Native ELF inspection produced diagnostics: ' + virtual)
    if re.search(r'\((?:AUDIT|DEPAUDIT)\)', headers.stdout):
        raise ValueError('ELF audit hooks need separate explicit review: ' + virtual)
    for search in re.findall(r'\((?:RPATH|RUNPATH)\).*\[(.*?)\]', headers.stdout):
        if any(part in search for part in ('/sources', '/tools', '/mnt/lfs', 'x86_64-lfs-linux-gnu')):
            raise ValueError('Build-only path embedded in native ELF search: ' + virtual)
    interpreters = re.findall(r'\[Requesting program interpreter: ([^\]]+)\]', headers.stdout)
    if not interpreters:
        return {'kind': 'elf-without-interpreter', 'file': virtual}
    if len(interpreters) != 1 or interpreters[0] not in (LOADER, CANONICAL_LOADER):
        raise ValueError('ELF interpreter differs from the frozen x86_64 loader: ' + virtual)
    interpreter = interpreters[0]
    _, canonical_loader = owned_file(image, interpreter, entries, executable=True)
    if canonical_loader != CANONICAL_LOADER:
        raise ValueError('ELF interpreter no longer resolves to the owned native loader')
    # Avoid executing the program entry point or its constructors. --list asks
    # the accepted image loader to resolve the actual executable dependency set.
    result = subprocess.run(['chroot', str(image), interpreter, '--list', virtual],
                            env=ENVIRONMENT, capture_output=True, text=True, timeout=30)
    if result.returncode or result.stderr:
        raise ValueError('Image loader cannot resolve ' + virtual + ': ' + repr(
            (result.returncode, result.stdout, result.stderr)))
    providers = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if re.fullmatch(r'linux-vdso\.so\.1 \(0x[0-9a-f]+\)', line):
            continue  # Kernel supplied mapping; never a package provider.
        match = re.fullmatch(r'(?:(\S+) => )?(/\S+) \(0x[0-9a-f]+\)', line)
        if not match:
            raise ValueError('Unclassified native loader output: ' + line)
        soname, provider = match.groups()
        _, resolved = owned_file(image, provider, entries)
        providers.append({'soname': soname, 'path': provider, 'owned_path': resolved})
    if not providers:
        raise ValueError('Dynamic executable has no measured image providers: ' + virtual)
    return {'kind': 'dynamic-executable', 'file': virtual, 'interpreter': interpreter,
            'loader_exit': result.returncode, 'providers': providers}


def audit(backend, image, entries):
    image = private_image(backend, image)
    if not entries:
        raise ValueError('Runtime audit requires verified native ownership inputs')
    before = package_database.snapshot(image / 'var/lib/dpkg')
    results, findings = [], []
    counts = {'data': 0, 'script': 0, 'dynamic-executable': 0, 'elf-without-interpreter': 0}
    for virtual, row in sorted(entries.items()):
        if not row.get('sha256'):
            continue
        try:
            result = executable(backend, image, virtual, entries)
            counts[result['kind']] += 1
            if result['kind'] in ('script', 'dynamic-executable'):
                results.append(result)
        except (ValueError, OSError, subprocess.SubprocessError) as error:
            findings.append({'file': virtual, 'problem': str(error)})
    if package_database.snapshot(image / 'var/lib/dpkg') != before:
        raise ValueError('Image database changed during runtime audit')
    return {'scope': 'Owned executable ELF loader resolution and executable shebang availability inside the image',
            'counts': counts, 'executables': results, 'findings': findings,
            'runtime_availability_check_passed': not findings,
            'package_solver_verified': False, 'complete_dependency_closure_verified': False,
            'limitations': ['ELFs without PT_INTERP are not independently executed; loaded libraries are checked in executable context.',
                           'Optional dlopen, internal tool/data/plugin paths and runtime symbol execution require separate tests.',
                           'This uses the builder guest kernel and does not verify native kernel boot.']}
