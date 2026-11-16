#!/usr/bin/env python3
"""Reuse the frozen cached model license and deliver fixed qualification sources."""
import json
import os
import phase2_candidate_vm as candidate
import sync_build

if __name__ == '__main__':
    candidate.owned()
    candidate.bases()
    model = json.loads((sync_build.ROOT/'config/phase2/local-model.lock.json').read_text())['model']
    source = sync_build.ROOT/'.local/phase2/upstream/qwen-LICENSE'
    assert source.is_file() and not source.is_symlink() and source.stat().st_size <= 65536
    assert sync_build.digest(source) == model['license_sha256']
    destination = sync_build.ROOT/'.local/sources/qwen-LICENSE'
    if not os.path.lexists(destination):
        os.link(source, destination)
    assert destination.is_file() and not destination.is_symlink()
    assert sync_build.digest(destination) == model['license_sha256']
    sync_build.vm.ssh_args = candidate.ssh
    sync_build.main(metadata_only=True, include_references=False,
        extra_metadata=('scripts/host/phase2-native-assistant-hook.py',
                        'scripts/host/phase2-native-assistant-control.py'),
        extra_sources=({'filename':'qwen-LICENSE','sha256':model['license_sha256']},))
