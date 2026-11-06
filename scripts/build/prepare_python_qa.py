#!/usr/bin/env python3
"""Prepare both native QA-transfer archives without changing installed Python.

Execution is gated on H11. Existing preparation state is preserved on failure;
the eventual transfer controller must revalidate this bundle before installing.
"""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from package_backend import PackageBackend
from python_qa_handoff import _layout, qa_dependencies
from python_qa_bundle import validate
from stage_package import digest

HERE = Path(__file__).resolve().parent
TARGET = Path('/mnt/lfs')
CACHE = Path('/var/cache/toddy/packages')
RECORDS = Path('/var/log/toddy/packages')


def read_control(backend, archive):
    fields = ('Package', 'Version', 'Architecture', 'Depends')
    return {field: backend.run('dpkg-deb', '-f', '/' + str(archive.relative_to(TARGET)),
                              field, capture_output=True, text=True).stdout.strip()
            for field in fields}


def main():
    subprocess.run([sys.executable, str(HERE / 'h11/require_gate.py')], check=True)
    backend = PackageBackend(TARGET)
    if not backend.native:
        raise SystemExit('QA preparation requires accepted native Dpkg')
    version, architecture, status = backend.run('dpkg-query', '-W', '-f=${Version}\t${Architecture}\t${Status}',
                                               'python', capture_output=True, text=True).stdout.split('\t')
    if status != 'install ok installed':
        raise SystemExit('Preserve and diagnose incomplete installed Python before preparation')
    if not re.fullmatch(r'[0-9][0-9A-Za-z.+:~_-]*', version) or architecture != 'amd64':
        raise SystemExit('Unexpected native Python identity')
    predecessor_stem = f'python_{version}_{architecture}'
    donor_path = RECORDS / (predecessor_stem + '.json')
    donor = json.loads(donor_path.read_text())
    original = CACHE / (predecessor_stem + '.deb')
    if not donor['installed'] or digest(original) != donor['archive_sha256']:
        raise SystemExit('Predecessor provenance mismatch')
    revision = re.search(r'\+toddy([1-9][0-9]*)$', version)
    successor = (version[:revision.start()] + '+toddy' + str(int(revision[1]) + 1)) if revision else version + '+toddy1'
    backend.run('dpkg', '--compare-versions', successor, 'gt', version)
    runtime = TARGET / 'sources/stage/h11-python-runtime'
    qa = TARGET / 'sources/stage/h11-python-tests'
    evidence = TARGET / 'sources/evidence/h11-python-qa-preparation'
    for path in (runtime, qa, evidence):
        if path.exists() or path.is_symlink() or path.resolve() != path:
            raise SystemExit('Preserve existing or redirected preparation state: ' + str(path))
    stems = [f'{name}_{successor}_{architecture}' for name in ('python', 'python-test-support')]
    for stem in stems:
        for path in (CACHE / (stem + '.deb'), RECORDS / (stem + '.json')):
            if path.exists() or path.is_symlink():
                raise SystemExit('Preserve existing successor artifact: ' + str(path))
    evidence.mkdir(mode=0o700, parents=True)
    before = digest(TARGET / 'var/lib/dpkg/status')
    copied = evidence / 'predecessor.deb'
    shutil.copy2(original, copied)
    if digest(copied) != donor['archive_sha256']:
        raise SystemExit('Copied predecessor archive mismatch')
    old_control = read_control(backend, copied)
    backend.run('dpkg-deb', '--raw-extract', '/' + str(copied.relative_to(TARGET)),
                '/' + str(runtime.relative_to(TARGET)))
    control_dir = runtime / 'DEBIAN'
    if any(path.name not in {'control', 'conffiles', 'md5sums'} for path in control_dir.iterdir()):
        raise SystemExit('Unexpected predecessor control program/data')
    conffiles = (control_dir / 'conffiles').read_text().splitlines() if (control_dir / 'conffiles').exists() else []
    shutil.rmtree(control_dir)
    split = _layout.partition(runtime, qa)
    notice = qa / 'usr/share/doc/python-test-support/copyright'
    notice.parent.mkdir(parents=True)
    shutil.copy2(runtime / 'usr/share/doc/python/copyright', notice)
    # Build both archives while the complete original remains installed.
    # No --install option is used here. Native compression stays bounded.
    for name, stage, dependencies in (('python', runtime, old_control['Depends']),
                                       ('python-test-support', qa, qa_dependencies(successor))):
        command = [sys.executable, str(HERE / 'stage_package.py'), name, successor, str(stage),
                   '--architecture', architecture, '--depends', dependencies, '--recipe', str(Path(__file__).resolve()),
                   '--compression-threads', '2']
        for row in donor['sources']:
            command += ['--source', row['filename']]
        if name == 'python':
            for path in conffiles:
                command += ['--conffile', path]
        else:
            command += ['--prepare-python-qa-handoff']
        subprocess.run(command, check=True)
    records, controls = [], [old_control]
    for stem in stems:
        record = json.loads((RECORDS / (stem + '.json')).read_text())
        archive = CACHE / (stem + '.deb')
        if digest(archive) != record['archive_sha256'] or record['installed']:
            raise SystemExit('Prepared archive identity/state mismatch')
        private = evidence / archive.name
        shutil.copy2(archive, private)
        if digest(private) != record['archive_sha256']:
            raise SystemExit('Copied successor archive mismatch')
        records.append(record)
        controls.append(read_control(backend, private))
    checked = validate(donor, *records, donor_record_sha256=digest(donor_path), controls=controls)
    if digest(TARGET / 'var/lib/dpkg/status') != before:
        raise SystemExit('Installed package state changed during archive-only preparation')
    result = {'predecessor': predecessor_stem, 'successors': stems, 'partition': split,
              'validation': checked, 'installed_status_unchanged': True,
              'archive_sha256': [donor['archive_sha256'], *(record['archive_sha256'] for record in records)],
              'production_transfer_complete': False}
    output = evidence / 'prepared.json'
    with output.open('x') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
