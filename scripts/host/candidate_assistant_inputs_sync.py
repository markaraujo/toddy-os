#!/usr/bin/env python3
"""Reuse the frozen cached model license and deliver fixed qualification sources."""
import json
import os
import sys
from pathlib import Path
import phase2_candidate_vm as candidate
import sync_build

def installer_source_pins():
    sys.path.insert(0,str(sync_build.ROOT))
    from runtime.installer.composition import SOURCES,source_path
    pins={}
    paths=[source_path(name) for name in sorted(SOURCES)]
    # Calamares and every other installer package source travel as a directory;
    # pin its complete non-cache file set as well as cross-directory SOURCES.
    paths.extend(path for path in (sync_build.ROOT/'runtime/installer').rglob('*')
        if path.is_file() and '__pycache__' not in path.parts and path.suffix!='.pyc')
    for path in paths:
        if path.resolve()!=path or not path.is_file() or path.is_symlink() or not path.is_relative_to(sync_build.ROOT):raise ValueError('Canonical installer source required')
        pins[path.relative_to(sync_build.ROOT).as_posix()]=sync_build.digest(path)
    return pins


def main():
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
    pins=installer_source_pins()
    sync_build.vm.ssh_args = candidate.ssh
    sync_build.main(metadata_only=True, include_references=False,
        extra_metadata=('runtime/installer','scripts/host/phase2-native-assistant-hook.py',
                        'scripts/host/phase2-native-assistant-control.py',*pins),
        required_metadata=pins,
        extra_sources=({'filename':'qwen-LICENSE','sha256':model['license_sha256']},))
    if installer_source_pins()!=pins:raise ValueError('Host installer source changed during controlled transfer; reconcile before packaging')
    print(json.dumps({'installer_source_files':len(pins),'source_map_sha256':sync_build.metadata_pin_identity(pins),
        'source_coherence_receipt':'/var/log/toddy/build/input-source-coherence-'+sync_build.metadata_pin_identity(pins)+'.json'}))


if __name__ == '__main__':main()
