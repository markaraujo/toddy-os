#!/usr/bin/env python3
"""Check frozen DB fixture application/reference matching without guest mutation."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/build'))
from apply_db_test_fixture import FIXTURES, apply_fixture
from locked_inputs import locked_source
from verify_db_tcl_tests import verify


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    cache = ROOT / '.local/sources'
    workspace = ROOT / '.local/probes'
    workspace.mkdir(parents=True, exist_ok=True)
    sources = Path(tempfile.mkdtemp(prefix='db-fixtures-', dir=workspace))
    native = sources / 'db-5.3.28'
    names = ['db5.3_5.3.28+dfsg2.orig.tar.xz',
             'db5.3_5.3.28+dfsg2-12.debian.tar.xz']
    for name in names + [name for name, _ in FIXTURES]:
        assert digest(cache / name) == locked_source(ROOT, name)['sha256']
        if name in names:
            (sources / name).symlink_to(cache / name)
        else:
            shutil.copyfile(cache / name, sources / name)
    with tarfile.open(sources / names[0]) as archive:
        for member in archive:
            if not member.name.startswith('db-5.3.28/test/tcl/') or not member.isfile():
                continue
            target = sources / member.name
            assert target.resolve().is_relative_to(native)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.extractfile(member).read())
    import subprocess
    with tarfile.open(sources / names[1]) as archive:
        patch = archive.extractfile('debian/patches/004-tclsleep.patch').read()
    subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-d', str(native)],
                   input=patch, check=True)
    for name, fixture in FIXTURES:
        apply_fixture(ROOT, sources, name, fixture)
    verify(ROOT, sources, native)
    snapshot = {str(p.relative_to(native)): digest(p)
                for p in (native / 'test/tcl').iterdir() if p.is_file()}
    assert len(snapshot) == 483
    for name, fixture in FIXTURES:
        apply_fixture(ROOT, sources, name, fixture)
    assert all(digest(native / path) == sha for path, sha in snapshot.items())

    negative = []
    for name, fixture in FIXTURES:
        target = native / fixture
        original = target.read_bytes()
        target.write_bytes(original + b'\n# unreviewed input\n')
        before = digest(target)
        try:
            apply_fixture(ROOT, sources, name, fixture)
        except SystemExit as error:
            assert str(error) == 'Unexpected DB fixture preimage'
        else:
            raise AssertionError('Changed preimage accepted')
        assert digest(target) == before
        target.write_bytes(original)
        negative.append(fixture + ': changed preimage rejected without mutation')

        patch_file = sources / name
        original_patch = patch_file.read_bytes()
        patch_file.write_bytes(original_patch + b'\n')
        try:
            apply_fixture(ROOT, sources, name, fixture)
        except SystemExit as error:
            assert str(error) == 'DB fixture patch integrity mismatch'
        else:
            raise AssertionError('Changed patch accepted')
        assert target.read_bytes() == original
        patch_file.write_bytes(original_patch)
        negative.append(fixture + ': changed patch rejected without mutation')

        preserved = target.with_suffix('.preserved')
        target.rename(preserved)
        target.symlink_to(preserved.name)
        try:
            apply_fixture(ROOT, sources, name, fixture)
        except SystemExit as error:
            assert str(error) == 'Fixture escapes source tree'
        else:
            raise AssertionError('Redirected fixture accepted')
        assert preserved.read_bytes() == original
        target.unlink()
        preserved.rename(target)
        negative.append(fixture + ': redirected fixture rejected without mutation')
    verify(ROOT, sources, native)
    result = {'verified_test_files': len(snapshot), 'idempotent': True,
              'negative_cases': negative, 'fixture': str(sources),
              'test_file_sha256': snapshot, 'guest_modified': False,
              'runtime_test_acceptance': False}
    output = ROOT / '.local/logs/h07-db-fixture-preflight.json'
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'report': str(output), 'sha256': digest(output),
                      'verified_files': len(snapshot), 'negative_cases': len(negative)}))


if __name__ == '__main__':
    main()
