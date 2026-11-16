#!/usr/bin/env python3
"""Transfer only six already-cached frozen voice inputs via verified guest sync."""
import hashlib
import json
import os
import phase2_candidate_vm as candidate
import sync_build

if __name__ == '__main__':
    candidate.owned()
    candidate.bases()
    rows = json.loads((sync_build.ROOT/'runtime/voice/native-inputs.lock.json').read_text())['artifacts']
    assert len(rows) == 6 and len({row['filename'] for row in rows}) == 6
    for row in rows:
        assert row['filename'] == os.path.basename(row['filename'])
        source = sync_build.ROOT/'.local/phase2/voice-native-inputs-1'/row['filename']
        assert source.is_file() and not source.is_symlink() and source.stat().st_size == row['size']
        assert sync_build.digest(source) == row['sha256']
        destination = sync_build.ROOT/'.local/sources'/row['filename']
        if not os.path.lexists(destination):
            os.link(source, destination)
        assert destination.is_file() and not destination.is_symlink()
        assert sync_build.digest(destination) == row['sha256']
    sync_build.vm.ssh_args = candidate.ssh
    sync_build.main(metadata_only=True, include_references=False,
        extra_metadata=('runtime/voice', 'tests/test_voice_process.py', 'tests/fixtures/voice/human'),
        extra_sources=rows)
