#!/usr/bin/env python3
"""Sync reviewed native candidate inputs under the existing exclusive guest lock."""
import phase2_candidate_vm as candidate
import sync_build
import base64
import hashlib
import json

if __name__ == '__main__':
    candidate.owned()
    candidate.bases()
    # Only frozen B01 npm archives/notices enter the candidate; never transfer
    # a cache directory, credential directory or other unselected local state.
    extra = ['assets/third-party', 'scripts/qualification', 'tests/test_voice_process.py']
    lock = json.loads((sync_build.ROOT/'runtime/engine/package-lock.json').read_text())
    for row in lock['packages'].values():
        if 'integrity' not in row:
            continue
        algorithm, encoded = row['integrity'].split('-', 1)
        expected = base64.b64decode(encoded, validate=True)
        assert algorithm == 'sha512' and len(expected) == 64
        name = '.local/sources/npm-'+expected.hex()+'.tgz'
        path = sync_build.ROOT/name
        assert not path.is_symlink() and path.is_file()
        assert hashlib.sha512(path.read_bytes()).digest() == expected
        extra.append(name)
    notices = json.loads((sync_build.ROOT/'config/phase2/engine-notices.lock.json').read_text())
    for row in notices['supplemental_notices']:
        assert len(row['sha256']) == 64 and all(c in '0123456789abcdef' for c in row['sha256'])
        name = '.local/phase2/engine-notices/'+row['sha256']
        path = sync_build.ROOT/name
        assert path.is_file() and not path.is_symlink() and sync_build.digest(path) == row['sha256']
        extra.append(name)
    sync_build.vm.ssh_args = candidate.ssh
    sync_build.main(metadata_only=True, include_references=False, extra_metadata=(
        'config/phase2', 'runtime', 'ui/phase2', 'assets/brand',
        'docs/evidence/B01-engine-components.json',
        'docs/evidence/B02-desktop-runtime-manifest.json',
        'tests/fixtures/voice/human', *extra))
