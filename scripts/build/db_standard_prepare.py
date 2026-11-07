#!/usr/bin/env python3
"""Prepare a private complete-suite view of an existing native DB test build.

This captures bytes, not build provenance or suite acceptance. The calling
recipe must retain its source/compile evidence and validate the eventual result.
No test suite, production build or package installation runs here.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile

from verify_db_tcl_tests import verify as verify_tcl

ROOT = Path(__file__).resolve().parents[2]
TARGET = Path('/mnt/lfs')
HELPER_SHA = '827f84ea724f12d6c91c5b215026e0e771a896423b67654690bd85ffaf08735c'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def inventory(source):
    """Exclude prior test output; preserve compiled wrappers and their libraries."""
    if source.resolve() != source or not source.is_dir():
        raise ValueError('Native source must be a physical directory')
    selected = []
    for path in sorted(source.iterdir()):
        if path.name.startswith('build-'):
            continue
        selected.append(path)
    build = source / 'build-test'
    if build.is_symlink() or not build.is_dir():
        raise ValueError('Missing or redirected native test build')
    for path in sorted(build.iterdir()):
        if path.name == '.libs' or (path.is_file() and (
                os.access(path, os.X_OK) or path.suffix in ('.h', '.la', '.a', '.lo', '.o') or
                path.name in ('Makefile', 'include.tcl', 'db_repsite.c'))):
            selected.append(path)
    rows = {}
    for top in selected:
        for path in [top, *sorted(top.rglob('*'))] if top.is_dir() else [top]:
            mode = path.lstat().st_mode
            if stat.S_ISDIR(mode):
                continue
            if not (stat.S_ISREG(mode) or stat.S_ISLNK(mode)):
                raise ValueError('Special native input: ' + str(path))
            if not path.resolve().is_relative_to(source) or not path.is_file():
                raise ValueError('External, broken or directory input link: ' + str(path))
            row = {'sha256': digest(path), 'mode': stat.S_IMODE(path.stat().st_mode)}
            if path.is_symlink():
                if os.path.isabs(os.readlink(path)):
                    raise ValueError('Nonportable absolute input link: ' + str(path))
                row['symlink'] = os.readlink(path)
            rows[str(path.relative_to(source))] = row
    for name in ('Makefile', 'config.status', 'db_config.h', 'include.tcl', 'cutest',
                 'db_repsite.c', 'db_repsite', '.libs/libdb-5.3.so'):
        if 'build-test/' + name not in rows:
            raise ValueError('Required compiled test input absent: ' + name)
    if digest(build / 'db_repsite.c') != HELPER_SHA:
        raise ValueError('Native test helper source differs from reviewed source')
    return rows


def copy_inputs(source, destination, rows):
    destination.mkdir()
    for name, row in rows.items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe relative input')
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if 'symlink' in row:
            path.symlink_to(row['symlink'])
        else:
            shutil.copy2(source / relative, path, follow_symlinks=False)
    for name, row in rows.items():
        path = destination / name
        if (not path.resolve().is_relative_to(destination) or digest(path) != row['sha256'] or
                stat.S_IMODE(path.stat().st_mode) != row['mode'] or
                path.is_symlink() != ('symlink' in row) or
                (path.is_symlink() and os.readlink(path) != row['symlink'])):
            raise ValueError('Copied native input changed: ' + name)


def save(path, data):
    with path.open('x') as stream:
        os.fchmod(stream.fileno(), 0o600)
        json.dump(data, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def prepare(source, *, root=ROOT, sources=TARGET / 'sources'):
    if os.geteuid() != 0:
        raise ValueError('Requires designated disposable guest root')
    subprocess.run(['bash', '-c',
                    'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    if source.resolve() != source or not source.is_relative_to(TARGET / 'sources'):
        raise ValueError('Source outside the designated physical build area')
    recovery = TARGET / 'sources/recovery'
    if recovery.resolve() != recovery or not recovery.is_dir():
        raise ValueError('Missing or redirected private generation area')
    if shutil.disk_usage(recovery).free < 40 * 1024**3:
        raise ValueError('Less than 40 GiB private build reserve')
    # Verify before allocating: an old uncorrected tree cannot become a new run.
    tcl = verify_tcl(root, sources, source)
    before = inventory(source)
    base = Path(tempfile.mkdtemp(prefix='db-standard-', dir=recovery))
    print('PREPARATION ' + str(base), flush=True)
    save(base / 'preparation.intent.json', {
        'source': str(source), 'created_at': datetime.now(timezone.utc).isoformat(),
        'source_inputs': before, 'preparation_module_sha256': digest(Path(__file__)),
        'suite_started': False, 'package_accepted': False})
    copied = base / 'source'
    copy_inputs(source, copied, before)
    # Production is a later, separately gated build; carry no prior artifacts.
    (copied / 'build-production').mkdir()
    if inventory(source) != before:
        raise ValueError('Source changed during preparation; preserve ' + str(base))
    if verify_tcl(root, sources, copied) != tcl:
        raise ValueError('Copied Tcl reference changed')
    recipes = root / 'scripts/build/h07'
    for name, target in (
            ('berkeley-db-standard-regression.tcl', copied / 'build-test/standard-regression.tcl'),
            ('berkeley-db-isolated-tests.sh', base / 'isolate.sh'),
            ('berkeley-db-isolation-probe.py', base / 'isolation-probe.py'),
            ('berkeley-db-isolated-driver.py', base / 'driver.py')):
        if target.exists() or target.is_symlink():
            raise ValueError('Preserve unexpected preparation destination: ' + str(target))
        shutil.copy2(recipes / name, target)
    namespaces = {name: os.readlink('/proc/self/ns/' + name) for name in ('pid', 'ipc', 'net', 'mnt')}
    save(base / 'outer-namespaces.json', namespaces)
    for name in ('tmp', 'var-tmp', 'shm'):
        path = base / 'runtime' / name
        path.mkdir(parents=True)
        path.chmod(0o1777)
    subprocess.run(['chroot', str(TARGET), '/usr/bin/chown', '-R', 'tester:tester',
                    '/' + str(copied.relative_to(TARGET))], check=True)
    files = {}
    for path in sorted(copied.rglob('*')):
        if path.is_file():
            if not path.resolve().is_relative_to(copied):
                raise ValueError('Escaping prepared input')
            row = {'sha256': digest(path)}
            if path.is_symlink():
                row['symlink'] = os.readlink(path)
            files[str(path.relative_to(copied))] = row
    inputs = {'fixture': str(base), 'source_files': files,
              'verified_tcl_files': len(tcl), 'copied_native_input_files': len(before),
              'preparation_intent_sha256': digest(base / 'preparation.intent.json'),
              'preparation_only': True, 'package_accepted': False,
              'test_entry_sha256': digest(copied / 'build-test/standard-regression.tcl'),
              'isolation_script_sha256': digest(base / 'isolate.sh'),
              'isolation_probe_sha256': digest(base / 'isolation-probe.py'),
              'outer_namespace_file_sha256': digest(base / 'outer-namespaces.json')}
    save(base / 'inputs.json', inputs)
    # The test identity needs traversal only after all input records are durable.
    base.chmod(0o755)
    with (base / 'isolation-probe.log').open('xb') as log:
        process = subprocess.run(['bash', str(base / 'isolate.sh'), str(base), 'probe'],
                                 stdout=log, stderr=subprocess.STDOUT, timeout=60)
    (base / 'isolation-probe.exit').write_text(str(process.returncode) + '\n')
    process.check_returncode()
    marker = 'toddy-bdb-' + base.name
    if ((TARGET / 'tmp' / marker).exists() or
            (base / 'runtime/tmp' / marker).read_text() != 'private namespace only\n' or
            namespaces != {name: os.readlink('/proc/self/ns/' + name) for name in namespaces}):
        raise ValueError('Private isolation probe affected outer state')
    if inventory(source) != before:
        raise ValueError('Original source changed during private probe')
    result = {'fixture': str(base), 'input_manifest_sha256': digest(base / 'inputs.json'),
              'copied_native_input_files': len(before), 'verified_tcl_files': len(tcl),
              'source_inputs_unchanged': True, 'outer_namespaces_unchanged': True,
              'outer_tmp_marker_absent': True, 'probe_exit': process.returncode,
              'isolation': json.loads((base / 'isolation-probe.json').read_text()),
              'suite_started': False, 'package_accepted': False}
    save(base / 'preparation.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=TARGET / 'sources/db-5.3.28')
    args = parser.parse_args()
    print(json.dumps(prepare(args.source)))


if __name__ == '__main__':
    main()
